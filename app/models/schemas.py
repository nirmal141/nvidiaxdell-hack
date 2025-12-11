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


class GlobalSearchRequest(BaseModel):
    """Request for global search across all videos."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=20, ge=1, le=100)


class GlobalSearchResult(BaseModel):
    """A single result from global search."""
    video_id: str
    video_name: str
    timestamp: float
    description: str
    relevance_score: float
    thumbnail_url: Optional[str] = None


class GlobalSearchResponse(BaseModel):
    """Response for global search."""
    query: str
    results: List[GlobalSearchResult]
    total_results: int
    answer: Optional[str] = None  # AI-generated summary of findings


class DetectedObject(BaseModel):
    """A single detected object."""
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2] normalized 0-1
    bbox_pixels: List[int]  # [x1, y1, x2, y2] in pixels


class DetectionResponse(BaseModel):
    """Response for object detection."""
    video_id: str
    timestamp: float
    detections: List[DetectedObject]
    frame_width: int
    frame_height: int
    inference_time_ms: float
    person_count: int = 0
    vehicle_count: int = 0


class DetectionRequest(BaseModel):
    """Request for object detection."""
    timestamp: float = 0.0
    confidence_threshold: float = 0.15  # Lower threshold for surveillance footage
    priority_only: bool = False  # Only security-relevant classes


class SegmentRequest(BaseModel):
    """Request for SAM2 segmentation."""
    timestamp: float = 0.0
    x: float  # Click X coordinate (0-1 normalized)
    y: float  # Click Y coordinate (0-1 normalized)


class SegmentResponse(BaseModel):
    """Response for SAM2 segmentation."""
    video_id: str
    timestamp: float
    polygon: List[List[float]]  # Polygon points for rendering
    area: float  # Mask area as percentage
    confidence: float

