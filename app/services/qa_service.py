"""Q&A service for video content retrieval and answer generation."""
import logging
from typing import List, Dict, Any, Optional, Callable
import asyncio
from dataclasses import dataclass

from .nim_client import VLMClient, EmbeddingClient, LLMClient, NIMClientError
from .vector_store import VectorStore, SearchResult
from .video_processor import VideoProcessor, FrameData, VideoLibrary
from ..models.schemas import ProcessingProgress, ProcessingStatus, TimestampSource, AnswerResponse

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of video processing."""
    video_id: str
    total_frames: int
    processed_frames: int
    success: bool
    error: Optional[str] = None


class VideoQAService:
    """
    Main service for video Q&A functionality.
    
    Orchestrates video processing, embedding generation, and answer retrieval.
    """
    
    def __init__(
        self,
        vlm_client: VLMClient,
        embedding_client: EmbeddingClient,
        llm_client: LLMClient,
        vector_store: VectorStore,
        video_processor: VideoProcessor,
        video_library: VideoLibrary
    ):
        """
        Initialize Q&A service.
        
        Args:
            vlm_client: Client for vision-language model
            embedding_client: Client for text embeddings
            llm_client: Client for LLM answers
            vector_store: Vector database
            video_processor: Video frame extractor
            video_library: Video file manager
        """
        self.vlm = vlm_client
        self.embedding = embedding_client
        self.llm = llm_client
        self.vector_store = vector_store
        self.processor = video_processor
        self.library = video_library
        
        self._processing_tasks: Dict[str, asyncio.Task] = {}
    
    async def process_video(
        self,
        video_id: str,
        progress_callback: Optional[Callable[[ProcessingProgress], None]] = None
    ) -> ProcessingResult:
        """
        Process a video: extract frames, generate descriptions, create embeddings, store in vector DB.
        
        Args:
            video_id: Video identifier
            progress_callback: Optional callback for progress updates
            
        Returns:
            ProcessingResult with status
        """
        video_info = self.library.get_video(video_id)
        if not video_info:
            return ProcessingResult(
                video_id=video_id,
                total_frames=0,
                processed_frames=0,
                success=False,
                error="Video not found"
            )
        
        video_path = video_info["path"]
        
        try:
            # Get metadata and count frames
            metadata = self.processor.get_metadata(video_path)
            total_frames = self.processor.count_sample_frames(video_path)
            
            # Update library with metadata
            self.library.update_video(video_id, {
                "duration": metadata.duration,
                "fps": metadata.fps,
                "width": metadata.width,
                "height": metadata.height,
                "total_frames": metadata.total_frames,
                "sample_frames": total_frames,
                "status": "processing"
            })
            
            # Delete any existing descriptions for this video
            self.vector_store.delete_video_descriptions(video_id)
            
            processed_count = 0
            batch_descriptions = []
            batch_size = 5  # Process in batches
            
            # Extract and process frames
            for frame_data in self.processor.extract_frames(video_path):
                try:
                    # Get VLM description
                    vlm_response = self.vlm.describe_frame(frame_data.image)
                    description = vlm_response.description
                    
                    # Get embedding
                    embed_response = self.embedding.embed_text(description)
                    embedding = embed_response.embedding
                    
                    batch_descriptions.append({
                        "timestamp": frame_data.timestamp,
                        "description": description,
                        "embedding": embedding
                    })
                    
                    processed_count += 1
                    
                    # Insert batch when full
                    if len(batch_descriptions) >= batch_size:
                        self.vector_store.insert_descriptions(video_id, batch_descriptions)
                        batch_descriptions = []
                    
                    # Report progress
                    if progress_callback:
                        progress = ProcessingProgress(
                            video_id=video_id,
                            status=ProcessingStatus.PROCESSING,
                            current_frame=processed_count,
                            total_frames=total_frames,
                            current_timestamp=frame_data.timestamp,
                            message=f"Processed frame at {self._format_timestamp(frame_data.timestamp)}"
                        )
                        progress_callback(progress)
                    
                    # Yield control for async
                    await asyncio.sleep(0)
                    
                except NIMClientError as e:
                    logger.warning(f"Error processing frame {frame_data.frame_number}: {e}")
                    continue
            
            # Insert remaining batch
            if batch_descriptions:
                self.vector_store.insert_descriptions(video_id, batch_descriptions)
            
            # Update library status
            self.library.update_video(video_id, {
                "status": "completed",
                "processed_frames": processed_count
            })
            
            # Final progress update
            if progress_callback:
                progress = ProcessingProgress(
                    video_id=video_id,
                    status=ProcessingStatus.COMPLETED,
                    current_frame=processed_count,
                    total_frames=total_frames,
                    current_timestamp=metadata.duration,
                    message="Processing complete!"
                )
                progress_callback(progress)
            
            return ProcessingResult(
                video_id=video_id,
                total_frames=total_frames,
                processed_frames=processed_count,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error processing video {video_id}: {e}")
            self.library.update_video(video_id, {"status": "failed"})
            
            if progress_callback:
                progress = ProcessingProgress(
                    video_id=video_id,
                    status=ProcessingStatus.FAILED,
                    message=str(e)
                )
                progress_callback(progress)
            
            return ProcessingResult(
                video_id=video_id,
                total_frames=0,
                processed_frames=0,
                success=False,
                error=str(e)
            )
    
    def ask_question(
        self,
        video_id: str,
        question: str,
        top_k: int = 5
    ) -> AnswerResponse:
        """
        Answer a question about a video.
        
        Args:
            video_id: Video identifier
            question: User's question
            top_k: Number of context items to retrieve
            
        Returns:
            AnswerResponse with answer and sources
        """
        # Embed the query
        try:
            query_embedding = self.embedding.embed_query(question).embedding
        except NIMClientError as e:
            logger.error(f"Error embedding query: {e}")
            return AnswerResponse(
                answer=f"Error processing query: {str(e)}",
                sources=[],
                video_id=video_id,
                question=question
            )
        
        # Search vector store
        search_results = self.vector_store.search(
            query_embedding=query_embedding,
            video_id=video_id,
            top_k=top_k
        )
        
        if not search_results:
            return AnswerResponse(
                answer="I couldn't find any relevant information in this video for your question. The video may not have been processed yet.",
                sources=[],
                video_id=video_id,
                question=question
            )
        
        # Format context for LLM
        context = [
            {
                "timestamp": r.timestamp,
                "description": r.description
            }
            for r in search_results
        ]
        
        # Generate answer
        try:
            llm_response = self.llm.generate_answer(question, context)
            answer = llm_response.content
        except NIMClientError as e:
            logger.error(f"Error generating answer: {e}")
            answer = f"Error generating answer: {str(e)}"
        
        # Format sources
        sources = [
            TimestampSource(
                timestamp=r.timestamp,
                description=r.description,
                relevance_score=r.score
            )
            for r in search_results
        ]
        
        return AnswerResponse(
            answer=answer,
            sources=sources,
            video_id=video_id,
            question=question
        )
    
    def get_processing_status(self, video_id: str) -> Optional[ProcessingProgress]:
        """Get current processing status for a video."""
        video_info = self.library.get_video(video_id)
        if not video_info:
            return None
        
        status_map = {
            "pending": ProcessingStatus.PENDING,
            "processing": ProcessingStatus.PROCESSING,
            "completed": ProcessingStatus.COMPLETED,
            "failed": ProcessingStatus.FAILED
        }
        
        return ProcessingProgress(
            video_id=video_id,
            status=status_map.get(video_info.get("status", "pending"), ProcessingStatus.PENDING),
            current_frame=video_info.get("processed_frames", 0),
            total_frames=video_info.get("sample_frames", 0),
            message=video_info.get("status", "pending")
        )
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds to MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
