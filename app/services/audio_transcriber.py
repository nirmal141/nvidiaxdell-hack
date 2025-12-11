"""Audio transcription service using faster-whisper."""
import os
import logging
import subprocess
import tempfile
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Check if faster-whisper is available
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. Run: pip install faster-whisper")


@dataclass
class TranscriptionSegment:
    """A segment of transcribed audio."""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Transcribed text


class AudioTranscriber:
    """
    Audio transcription using faster-whisper.
    
    Extracts audio from video and transcribes with timestamps.
    """
    
    _instance: Optional['AudioTranscriber'] = None
    _model = None
    
    # Model options: tiny, base, small, medium, large-v2
    MODEL_SIZE = os.environ.get("WHISPER_MODEL", "base")
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the transcriber."""
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not available - transcription disabled")
            return
            
        if AudioTranscriber._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        logger.info(f"Loading Whisper model: {self.MODEL_SIZE}")
        
        # Use GPU if available
        device = "cuda"
        compute_type = "float16"
        
        try:
            AudioTranscriber._model = WhisperModel(
                self.MODEL_SIZE,
                device=device,
                compute_type=compute_type
            )
            logger.info(f"Whisper model loaded on GPU")
        except Exception as e:
            logger.warning(f"GPU failed, falling back to CPU: {e}")
            AudioTranscriber._model = WhisperModel(
                self.MODEL_SIZE,
                device="cpu",
                compute_type="int8"
            )
            logger.info("Whisper model loaded on CPU")
    
    def extract_audio(self, video_path: str) -> Optional[str]:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to temporary audio file, or None if failed
        """
        # Create temp file for audio
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_audio.close()
        
        try:
            # Use ffmpeg to extract audio
            cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # WAV format
                "-ar", "16000",  # 16kHz sample rate (Whisper expects this)
                "-ac", "1",  # Mono
                temp_audio.name
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )
            
            if result.returncode != 0:
                logger.error(f"ffmpeg error: {result.stderr}")
                os.unlink(temp_audio.name)
                return None
                
            return temp_audio.name
            
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg timed out")
            os.unlink(temp_audio.name)
            return None
        except FileNotFoundError:
            logger.error("ffmpeg not found - please install it")
            os.unlink(temp_audio.name)
            return None
    
    def transcribe(self, video_path: str) -> List[TranscriptionSegment]:
        """
        Transcribe audio from a video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of transcription segments with timestamps
        """
        if not WHISPER_AVAILABLE or AudioTranscriber._model is None:
            logger.warning("Whisper not available")
            return []
        
        # Extract audio
        logger.info(f"Extracting audio from {video_path}")
        audio_path = self.extract_audio(video_path)
        
        if not audio_path:
            logger.warning("Failed to extract audio")
            return []
        
        try:
            # Transcribe
            logger.info("Transcribing audio...")
            segments, info = AudioTranscriber._model.transcribe(
                audio_path,
                beam_size=5,
                word_timestamps=False,  # Segment-level is enough
                vad_filter=True,  # Filter out silence
            )
            
            logger.info(f"Detected language: {info.language} ({info.language_probability:.2%})")
            
            # Convert to our format
            result = []
            for segment in segments:
                result.append(TranscriptionSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip()
                ))
            
            logger.info(f"Transcribed {len(result)} segments")
            return result
            
        finally:
            # Clean up temp file
            if os.path.exists(audio_path):
                os.unlink(audio_path)
    
    def transcribe_segments(
        self, 
        video_path: str, 
        segment_duration: float = 30.0
    ) -> List[TranscriptionSegment]:
        """
        Transcribe and group into fixed-duration segments for vector store.
        
        Args:
            video_path: Path to video file
            segment_duration: Duration of each segment in seconds
            
        Returns:
            List of consolidated segments
        """
        raw_segments = self.transcribe(video_path)
        
        if not raw_segments:
            return []
        
        # Group into larger segments
        consolidated = []
        current_text = []
        current_start = 0.0
        current_end = 0.0
        
        for seg in raw_segments:
            # Start new segment if needed
            if not current_text:
                current_start = seg.start
            
            current_text.append(seg.text)
            current_end = seg.end
            
            # If we've exceeded segment duration, save and reset
            if current_end - current_start >= segment_duration:
                consolidated.append(TranscriptionSegment(
                    start=current_start,
                    end=current_end,
                    text=" ".join(current_text)
                ))
                current_text = []
        
        # Don't forget last segment
        if current_text:
            consolidated.append(TranscriptionSegment(
                start=current_start,
                end=current_end,
                text=" ".join(current_text)
            ))
        
        return consolidated


# Singleton accessor
_transcriber: Optional[AudioTranscriber] = None

def get_audio_transcriber() -> AudioTranscriber:
    """Get or create audio transcriber instance."""
    global _transcriber
    if _transcriber is None:
        _transcriber = AudioTranscriber()
    return _transcriber
