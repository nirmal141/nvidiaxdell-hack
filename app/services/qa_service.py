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
            
            # === AUDIO TRANSCRIPTION ===
            try:
                from .audio_transcriber import get_audio_transcriber, WHISPER_AVAILABLE
                
                if WHISPER_AVAILABLE:
                    if progress_callback:
                        progress = ProcessingProgress(
                            video_id=video_id,
                            status=ProcessingStatus.PROCESSING,
                            current_frame=processed_count,
                            total_frames=total_frames,
                            message="Transcribing audio..."
                        )
                        progress_callback(progress)
                    
                    transcriber = get_audio_transcriber()
                    segments = transcriber.transcribe_segments(video_path, segment_duration=10.0)
                    
                    # Store transcription segments
                    audio_descriptions = []
                    for seg in segments:
                        if not seg.text.strip():
                            continue
                        
                        # Prefix with [AUDIO] for clarity
                        description = f"[AUDIO] {seg.text}"
                        
                        try:
                            embed_response = self.embedding.embed_text(description)
                            audio_descriptions.append({
                                "timestamp": seg.start,
                                "description": description,
                                "embedding": embed_response.embedding,
                                "source_type": "audio"
                            })
                        except NIMClientError as e:
                            logger.warning(f"Error embedding audio segment: {e}")
                            continue
                    
                    if audio_descriptions:
                        self.vector_store.insert_descriptions(video_id, audio_descriptions)
                        logger.info(f"Added {len(audio_descriptions)} audio segments for {video_id}")
                    
                    await asyncio.sleep(0)
            except ImportError:
                logger.debug("Audio transcription not available")
            except Exception as e:
                logger.warning(f"Audio transcription failed: {e}")
            
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
    
    def global_search(
        self,
        query: str,
        top_k: int = 20,
        generate_answer: bool = True
    ) -> Dict[str, Any]:
        """
        Search across ALL videos in the database.
        
        Args:
            query: Search query
            top_k: Number of results to return
            generate_answer: Whether to generate an AI summary
            
        Returns:
            Dict with results and optional AI-generated answer
        """
        # Embed the query
        try:
            query_embedding = self.embedding.embed_query(query).embedding
        except NIMClientError as e:
            logger.error(f"Error embedding query: {e}")
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "answer": None,
                "error": str(e)
            }
        
        # Search across ALL videos (no video_id filter)
        # Fetch more results for deduplication headroom
        search_results = self.vector_store.search(
            query_embedding=query_embedding,
            video_id=None,  # Search all videos
            top_k=top_k * 3  # Get extra for deduplication
        )
        
        if not search_results:
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "answer": "No matching content found in any processed videos."
            }
        
        # === DEDUPLICATION ===
        # Group results from same video within time window (30 seconds)
        # Keep only the best match per time window
        TIME_WINDOW = 30.0  # seconds
        
        deduplicated = []
        seen_windows = {}  # (video_id, window_index) -> best result
        
        for r in search_results:
            window_idx = int(r.timestamp // TIME_WINDOW)
            key = (r.video_id, window_idx)
            
            if key not in seen_windows:
                seen_windows[key] = r
                deduplicated.append(r)
            # Keep the one with higher score (earlier results have higher scores from vector search)
        
        # Limit to top_k after deduplication
        deduplicated = deduplicated[:top_k]
        
        # Enrich results with video metadata
        enriched_results = []
        for r in deduplicated:
            video_info = self.library.get_video(r.video_id)
            video_name = video_info.get("name", r.video_id) if video_info else r.video_id
            
            enriched_results.append({
                "video_id": r.video_id,
                "video_name": video_name,
                "timestamp": r.timestamp,
                "description": r.description,
                "relevance_score": r.score,
                "thumbnail_url": f"/api/videos/{r.video_id}/thumbnail" if video_info else None
            })
        
        # Generate AI summary if requested
        answer = None
        if generate_answer and enriched_results:
            try:
                # Format context with video sources
                context_items = [
                    {
                        "timestamp": r["timestamp"],
                        "description": f"[{r['video_name']}] {r['description']}"
                    }
                    for r in enriched_results[:10]  # Use top 10 for answer
                ]
                
                # Custom system prompt for global search
                system_prompt = """You are an AI assistant helping analyze surveillance/video footage.
You are given descriptions from MULTIPLE videos at specific timestamps.
Answer the user's query based on the provided context.
Always cite which video and timestamp you're referring to.
Format: "In [video_name] at [MM:SS], ..." """
                
                llm_response = self.llm.generate_answer(
                    question=query,
                    context=context_items,
                    system_prompt=system_prompt
                )
                answer = llm_response.content
            except NIMClientError as e:
                logger.error(f"Error generating answer: {e}")
                answer = None
        
        return {
            "query": query,
            "results": enriched_results,
            "total_results": len(enriched_results),
            "answer": answer
        }

