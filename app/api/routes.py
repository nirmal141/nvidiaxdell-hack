"""FastAPI routes and WebSocket handlers for Video Q&A API."""
import os
import uuid
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse

from ..models.schemas import (
    VideoInfo, VideoUploadResponse, VideoListResponse,
    ProcessingProgress, ProcessingStatus, QuestionRequest, AnswerResponse
)
from ..config import config
from ..services.video_processor import VideoProcessor, VideoLibrary
from ..services.vector_store import VectorStore
from ..services.nim_client import VLMClient, EmbeddingClient, LLMClient, NIMClientFactory
from ..services.qa_service import VideoQAService

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances (initialized lazily)
_qa_service: Optional[VideoQAService] = None
_video_library: Optional[VideoLibrary] = None

# WebSocket connections for progress updates
active_connections: Dict[str, WebSocket] = {}


def get_video_library() -> VideoLibrary:
    """Get or create video library instance."""
    global _video_library
    if _video_library is None:
        _video_library = VideoLibrary(str(config.videos_dir))
    return _video_library


def get_qa_service() -> VideoQAService:
    """Get or create QA service instance."""
    global _qa_service
    if _qa_service is None:
        vlm_client = NIMClientFactory.create_vlm_client(config)
        embedding_client = NIMClientFactory.create_embedding_client(config)
        llm_client = NIMClientFactory.create_llm_client(config)
        vector_store = VectorStore(
            db_path=config.milvus.db_path,
            collection_name=config.milvus.collection_name,
            embedding_dim=config.milvus.embedding_dim
        )
        video_processor = VideoProcessor(sample_interval=config.video.frame_sample_interval)
        
        _qa_service = VideoQAService(
            vlm_client=vlm_client,
            embedding_client=embedding_client,
            llm_client=llm_client,
            vector_store=vector_store,
            video_processor=video_processor,
            video_library=get_video_library()
        )
    return _qa_service


@router.get("/api/videos", response_model=VideoListResponse)
async def list_videos():
    """List all available videos."""
    library = get_video_library()
    videos = library.list_videos()
    
    video_infos = []
    for v in videos:
        video_infos.append(VideoInfo(
            id=v.get("id", ""),
            name=v.get("name", v.get("filename", "")),
            filename=v.get("filename", ""),
            duration=v.get("duration"),
            frame_count=v.get("total_frames"),
            processed_frames=v.get("processed_frames", 0),
            status=ProcessingStatus(v.get("status", "pending")),
            thumbnail_url=f"/api/videos/{v.get('id')}/thumbnail" if v.get("thumbnail") else None
        ))
    
    return VideoListResponse(videos=video_infos, total=len(video_infos))


@router.post("/api/videos/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """Upload a new video file."""
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in config.video.supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {config.video.supported_formats}"
        )
    
    # Generate unique ID and filename
    video_id = str(uuid.uuid4())[:8]
    safe_filename = f"{video_id}_{Path(file.filename).stem}{ext}"
    file_path = config.videos_dir / safe_filename
    
    try:
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Get video metadata
        processor = VideoProcessor()
        metadata = processor.get_metadata(str(file_path))
        
        # Generate thumbnail
        thumbnail_path = config.videos_dir / f"{video_id}_thumb.jpg"
        processor.generate_thumbnail(str(file_path), str(thumbnail_path))
        
        # Add to library
        library = get_video_library()
        video_info = library.add_video(video_id, safe_filename, {
            "name": Path(file.filename).stem,
            "duration": metadata.duration,
            "fps": metadata.fps,
            "width": metadata.width,
            "height": metadata.height,
            "total_frames": metadata.total_frames,
            "thumbnail": str(thumbnail_path)
        })
        
        return VideoUploadResponse(
            success=True,
            video=VideoInfo(
                id=video_id,
                name=Path(file.filename).stem,
                filename=safe_filename,
                duration=metadata.duration,
                frame_count=metadata.total_frames,
                status=ProcessingStatus.PENDING,
                thumbnail_url=f"/api/videos/{video_id}/thumbnail"
            )
        )
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        # Cleanup on failure
        if file_path.exists():
            file_path.unlink()
        return VideoUploadResponse(success=False, error=str(e))


@router.get("/api/videos/{video_id}")
async def get_video(video_id: str):
    """Get video info by ID."""
    library = get_video_library()
    video = library.get_video(video_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return VideoInfo(
        id=video.get("id", ""),
        name=video.get("name", video.get("filename", "")),
        filename=video.get("filename", ""),
        duration=video.get("duration"),
        frame_count=video.get("total_frames"),
        processed_frames=video.get("processed_frames", 0),
        status=ProcessingStatus(video.get("status", "pending")),
        thumbnail_url=f"/api/videos/{video_id}/thumbnail" if video.get("thumbnail") else None
    )


@router.get("/api/videos/{video_id}/stream")
async def stream_video(video_id: str):
    """Stream video file."""
    library = get_video_library()
    video = library.get_video(video_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    file_path = Path(video.get("path", ""))
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        str(file_path),
        media_type="video/mp4",
        filename=video.get("filename", "video.mp4")
    )


@router.get("/api/videos/{video_id}/thumbnail")
async def get_thumbnail(video_id: str):
    """Get video thumbnail."""
    library = get_video_library()
    video = library.get_video(video_id)
    
    if not video or not video.get("thumbnail"):
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    thumbnail_path = Path(video.get("thumbnail", ""))
    if not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found")
    
    return FileResponse(str(thumbnail_path), media_type="image/jpeg")


@router.post("/api/videos/{video_id}/process")
async def start_processing(video_id: str, background_tasks: BackgroundTasks):
    """Start processing a video."""
    library = get_video_library()
    video = library.get_video(video_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.get("status") == "processing":
        raise HTTPException(status_code=400, detail="Video is already being processed")
    
    # Start processing in background
    async def process_with_updates():
        qa_service = get_qa_service()
        
        def progress_callback(progress: ProcessingProgress):
            # Send progress to connected WebSocket clients
            asyncio.create_task(broadcast_progress(video_id, progress))
        
        await qa_service.process_video(video_id, progress_callback)
    
    background_tasks.add_task(process_with_updates)
    
    return {"message": "Processing started", "video_id": video_id}


@router.get("/api/videos/{video_id}/status")
async def get_processing_status(video_id: str):
    """Get processing status for a video."""
    qa_service = get_qa_service()
    status = qa_service.get_processing_status(video_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return status


@router.post("/api/videos/{video_id}/ask", response_model=AnswerResponse)
async def ask_question(video_id: str, request: QuestionRequest):
    """Ask a question about a video."""
    library = get_video_library()
    video = library.get_video(video_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail="Video must be processed before asking questions"
        )
    
    qa_service = get_qa_service()
    answer = qa_service.ask_question(video_id, request.question)
    
    return answer


@router.delete("/api/videos/{video_id}")
async def delete_video(video_id: str):
    """Delete a video and its data."""
    library = get_video_library()
    video = library.get_video(video_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Delete vector data
    qa_service = get_qa_service()
    qa_service.vector_store.delete_video_descriptions(video_id)
    
    # Delete thumbnail
    if video.get("thumbnail"):
        thumb_path = Path(video.get("thumbnail", ""))
        if thumb_path.exists():
            thumb_path.unlink()
    
    # Delete from library (also deletes video file)
    library.delete_video(video_id)
    
    return {"message": "Video deleted", "video_id": video_id}


# WebSocket for real-time progress updates
@router.websocket("/ws/progress/{video_id}")
async def websocket_progress(websocket: WebSocket, video_id: str):
    """WebSocket endpoint for real-time processing progress."""
    await websocket.accept()
    active_connections[video_id] = websocket
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        if video_id in active_connections:
            del active_connections[video_id]


async def broadcast_progress(video_id: str, progress: ProcessingProgress):
    """Broadcast progress update to connected WebSocket clients."""
    if video_id in active_connections:
        try:
            await active_connections[video_id].send_json(progress.model_dump())
        except Exception as e:
            logger.warning(f"Error sending progress: {e}")
            if video_id in active_connections:
                del active_connections[video_id]
