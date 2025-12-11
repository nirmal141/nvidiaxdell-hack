"""Video processing service with hardware-accelerated frame extraction."""
import cv2
import numpy as np
from pathlib import Path
from typing import Generator, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class FrameData:
    """Data for an extracted video frame."""
    frame_number: int
    timestamp: float
    image: np.ndarray


@dataclass
class VideoMetadata:
    """Video file metadata."""
    path: str
    width: int
    height: int
    fps: float
    total_frames: int
    duration: float
    codec: str


class VideoProcessor:
    """
    Video processor using OpenCV with CUDA backend when available.
    
    Extracts frames at configurable intervals for VLM processing.
    """
    
    def __init__(self, sample_interval: float = 1.0, use_cuda: bool = True):
        """
        Initialize video processor.
        
        Args:
            sample_interval: Time in seconds between frame samples
            use_cuda: Whether to use CUDA acceleration if available
        """
        self.sample_interval = sample_interval
        self.use_cuda = use_cuda and self._check_cuda_available()
        
        if self.use_cuda:
            logger.info("CUDA acceleration enabled for video processing")
        else:
            logger.info("Using CPU for video processing")
    
    @staticmethod
    def _check_cuda_available() -> bool:
        """Check if CUDA is available for OpenCV."""
        try:
            count = cv2.cuda.getCudaEnabledDeviceCount()
            return count > 0
        except:
            return False
    
    def get_metadata(self, video_path: str) -> VideoMetadata:
        """
        Get video file metadata.
        
        Args:
            video_path: Path to video file
            
        Returns:
            VideoMetadata object
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        try:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            return VideoMetadata(
                path=video_path,
                width=width,
                height=height,
                fps=fps,
                total_frames=total_frames,
                duration=duration,
                codec=codec
            )
        finally:
            cap.release()
    
    def extract_frames(
        self, 
        video_path: str,
        start_time: float = 0,
        end_time: Optional[float] = None
    ) -> Generator[FrameData, None, None]:
        """
        Extract frames from video at configured sample interval.
        
        Args:
            video_path: Path to video file
            start_time: Start time in seconds
            end_time: End time in seconds (None for entire video)
            
        Yields:
            FrameData objects for each sampled frame
        """
        metadata = self.get_metadata(video_path)
        
        if end_time is None:
            end_time = metadata.duration
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        try:
            # Calculate frame numbers to extract
            start_frame = int(start_time * metadata.fps)
            end_frame = int(end_time * metadata.fps)
            frame_interval = int(self.sample_interval * metadata.fps)
            
            if frame_interval < 1:
                frame_interval = 1
            
            current_frame = start_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            
            while current_frame < end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                timestamp = current_frame / metadata.fps
                
                yield FrameData(
                    frame_number=current_frame,
                    timestamp=timestamp,
                    image=frame_rgb
                )
                
                # Skip to next sample frame
                current_frame += frame_interval
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                
        finally:
            cap.release()
    
    def count_sample_frames(self, video_path: str) -> int:
        """
        Count how many frames will be sampled from a video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Number of frames that will be extracted
        """
        metadata = self.get_metadata(video_path)
        frame_interval = int(self.sample_interval * metadata.fps)
        if frame_interval < 1:
            frame_interval = 1
        return (metadata.total_frames + frame_interval - 1) // frame_interval
    
    def generate_thumbnail(
        self, 
        video_path: str, 
        output_path: str,
        size: Tuple[int, int] = (320, 180),
        timestamp: float = 1.0
    ) -> str:
        """
        Generate a thumbnail image from the video.
        
        Args:
            video_path: Path to video file
            output_path: Path to save thumbnail
            size: Thumbnail size (width, height)
            timestamp: Time in seconds to capture thumbnail
            
        Returns:
            Path to saved thumbnail
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if not ret:
                # Try first frame if timestamp fails
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            
            if ret:
                # Resize to thumbnail size
                thumbnail = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
                cv2.imwrite(output_path, thumbnail)
                return output_path
            else:
                raise ValueError("Could not read frame for thumbnail")
        finally:
            cap.release()


class VideoLibrary:
    """Manages video files and their metadata."""
    
    def __init__(self, videos_dir: str, metadata_file: str = "videos_metadata.json"):
        """
        Initialize video library.
        
        Args:
            videos_dir: Directory containing video files
            metadata_file: Name of metadata JSON file
        """
        self.videos_dir = Path(videos_dir)
        self.metadata_file = self.videos_dir / metadata_file
        self.videos: Dict[str, Dict[str, Any]] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """Load video metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.videos = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}")
                self.videos = {}
    
    def _save_metadata(self):
        """Save video metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.videos, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save metadata: {e}")
    
    def add_video(
        self, 
        video_id: str, 
        filename: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a video to the library.
        
        Args:
            video_id: Unique identifier for the video
            filename: Filename in videos directory
            metadata: Optional additional metadata
            
        Returns:
            Video info dictionary
        """
        video_info = {
            "id": video_id,
            "filename": filename,
            "path": str(self.videos_dir / filename),
            "status": "pending",
            "processed_frames": 0,
            **(metadata or {})
        }
        self.videos[video_id] = video_info
        self._save_metadata()
        return video_info
    
    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video info by ID."""
        video = self.videos.get(video_id)
        if video:
            # Fix path to be relative to current videos_dir (handles Docker mount points)
            video = video.copy()
            filename = video.get("filename", "")
            video["path"] = str(self.videos_dir / filename)
            # Also fix thumbnail path if present
            if video.get("thumbnail"):
                thumb_filename = Path(video["thumbnail"]).name
                video["thumbnail"] = str(self.videos_dir / thumb_filename)
        return video
    
    def update_video(self, video_id: str, updates: Dict[str, Any]):
        """Update video metadata."""
        if video_id in self.videos:
            self.videos[video_id].update(updates)
            self._save_metadata()
    
    def list_videos(self) -> list:
        """List all videos in library."""
        return list(self.videos.values())
    
    def delete_video(self, video_id: str) -> bool:
        """Delete a video from library."""
        if video_id in self.videos:
            video_path = Path(self.videos[video_id].get("path", ""))
            if video_path.exists():
                video_path.unlink()
            del self.videos[video_id]
            self._save_metadata()
            return True
        return False
