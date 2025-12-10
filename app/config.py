"""Configuration settings for Video Q&A Application."""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NIMConfig:
    """NVIDIA NIM endpoint configuration."""
    vlm_url: str = "http://localhost:8000/v1"
    vlm_model: str = "nvidia/vila"
    
    embedding_url: str = "http://localhost:8001/v1"
    embedding_model: str = "nvidia/nv-embed-qa"
    
    llm_url: str = "http://localhost:8002/v1"
    llm_model: str = "meta/llama"
    
    timeout: int = 120
    max_retries: int = 3


@dataclass
class VideoConfig:
    """Video processing configuration."""
    frame_sample_interval: float = 1.0  # Extract 1 frame per second
    max_frames_per_batch: int = 10
    supported_formats: tuple = (".mp4", ".avi", ".mkv", ".mov", ".webm")
    thumbnail_size: tuple = (320, 180)


@dataclass
class MilvusConfig:
    """Milvus Lite vector database configuration."""
    db_path: str = "./data/milvus/video_qa.db"
    collection_name: str = "video_descriptions"
    embedding_dim: int = 1024  # NV-Embed-QA dimension
    index_type: str = "FLAT"
    metric_type: str = "COSINE"
    top_k: int = 5


@dataclass 
class AppConfig:
    """Main application configuration."""
    # Base paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data")
    videos_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "videos")
    static_dir: Path = field(default_factory=lambda: Path(__file__).parent / "static")
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = True
    
    # Component configs
    nim: NIMConfig = field(default_factory=NIMConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    milvus: MilvusConfig = field(default_factory=MilvusConfig)
    
    def __post_init__(self):
        """Ensure directories exist."""
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        Path(self.milvus.db_path).parent.mkdir(parents=True, exist_ok=True)


# Global config instance
config = AppConfig()
