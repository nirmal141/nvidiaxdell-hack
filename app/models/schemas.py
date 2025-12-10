"""Pydantic models for API request/response schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    """Video processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoInfo(BaseModel):
    """Video metadata."""
    id: str
    name: str
    filename: str
    duration: Optional[float] = None
    frame_count: Optional[int] = None
    processed_frames: int = 0
    status: ProcessingStatus = ProcessingStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VideoUploadResponse(BaseModel):
    """Response after video upload."""
    success: bool
    video: Optional[VideoInfo] = None
    error: Optional[str] = None


class ProcessingProgress(BaseModel):
    """Real-time processing progress."""
    video_id: str
    status: ProcessingStatus
    current_frame: int = 0
    total_frames: int = 0
    current_timestamp: float = 0.0
    message: str = ""
    
    @property
    def progress_percent(self) -> float:
        if self.total_frames == 0:
            return 0.0
        return (self.current_frame / self.total_frames) * 100


class QuestionRequest(BaseModel):
    """User question about a video."""
    question: str = Field(..., min_length=1, max_length=1000)
    video_id: str


class TimestampSource(BaseModel):
    """A source timestamp with description."""
    timestamp: float
    description: str
    relevance_score: float


class AnswerResponse(BaseModel):
    """Response to a user question."""
    answer: str
    sources: List[TimestampSource] = []
    video_id: str
    question: str


class FrameDescription(BaseModel):
    """Description of a single video frame."""
    video_id: str
    frame_number: int
    timestamp: float
    description: str
    embedding: Optional[List[float]] = None


class VideoListResponse(BaseModel):
    """List of available videos."""
    videos: List[VideoInfo]
    total: int
