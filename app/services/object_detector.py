"""Object detection service using YOLOv8 on GPU."""
import torch
from ultralytics import YOLO
import numpy as np
from typing import List, Optional, Dict, Any
import logging
from dataclasses import dataclass
from PIL import Image
import cv2

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Single object detection result."""
    class_id: int
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2] normalized 0-1
    bbox_pixels: List[int]  # [x1, y1, x2, y2] in pixels


@dataclass
class DetectionResult:
    """Detection results for a frame."""
    detections: List[Detection]
    frame_width: int
    frame_height: int
    inference_time_ms: float


class ObjectDetector:
    """Object detector using YOLOv8 on GPU."""
    
    _instance: Optional['ObjectDetector'] = None
    _model = None
    
    # Security-relevant classes to highlight
    PRIORITY_CLASSES = {
        0: "person",
        1: "bicycle", 
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck",
        24: "backpack",
        26: "handbag",
        28: "suitcase",
        39: "bottle",
        41: "cup",
        43: "knife",
        67: "cell phone",
        73: "laptop",
    }
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the detector."""
        if ObjectDetector._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load YOLOv8 model."""
        logger.info("Loading YOLOv8x model (high accuracy)...")
        
        # Use YOLOv8x (extra-large) for best accuracy on surveillance footage
        ObjectDetector._model = YOLO("yolov8x.pt")
        
        # Move to GPU if available
        if torch.cuda.is_available():
            ObjectDetector._model.to("cuda")
            logger.info("YOLOv8x loaded on GPU")
        else:
            logger.info("YOLOv8x loaded on CPU")
    
    def detect(
        self, 
        frame: np.ndarray, 
        confidence_threshold: float = 0.15,
        priority_only: bool = False
    ) -> DetectionResult:
        """
        Detect objects in a frame.
        
        Args:
            frame: RGB numpy array (H, W, 3)
            confidence_threshold: Minimum confidence score
            priority_only: If True, only return security-relevant classes
            
        Returns:
            DetectionResult with detected objects
        """
        import time
        start = time.time()
        
        height, width = frame.shape[:2]
        
        # Run YOLO inference with lower threshold for people
        results = self._model(frame, conf=confidence_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for i, box in enumerate(boxes):
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # Filter to priority classes if requested
                if priority_only and class_id not in self.PRIORITY_CLASSES:
                    continue
                
                # Get class name
                class_name = self._model.names.get(class_id, f"class_{class_id}")
                
                # Get bounding box (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                detections.append(Detection(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence,
                    bbox=[x1/width, y1/height, x2/width, y2/height],  # Normalized
                    bbox_pixels=[int(x1), int(y1), int(x2), int(y2)]
                ))
        
        # Add fire detection (YOLO doesn't detect fire by default)
        fire_detections = self._detect_fire(frame)
        detections.extend(fire_detections)
        
        inference_time = (time.time() - start) * 1000
        
        return DetectionResult(
            detections=detections,
            frame_width=width,
            frame_height=height,
            inference_time_ms=inference_time
        )
    
    def _detect_fire(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect fire using color analysis (orange/red/yellow regions).
        YOLO doesn't detect fire, so we use color-based detection.
        """
        height, width = frame.shape[:2]
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        
        # Define fire color ranges (orange, red, yellow)
        # Lower red range
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        # Upper red range  
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        # Orange range
        lower_orange = np.array([10, 100, 150])
        upper_orange = np.array([25, 255, 255])
        # Yellow range
        lower_yellow = np.array([25, 100, 150])
        upper_yellow = np.array([35, 255, 255])
        
        # Create masks
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_orange = cv2.inRange(hsv, lower_orange, upper_orange)
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Combine masks
        fire_mask = mask_red1 | mask_red2 | mask_orange | mask_yellow
        
        # Find contours
        contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        fire_detections = []
        min_fire_area = (width * height) * 0.002  # Minimum 0.2% of frame
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_fire_area:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate confidence based on area and color intensity
            confidence = min(0.9, 0.3 + (area / (width * height)) * 2)
            
            fire_detections.append(Detection(
                class_id=999,  # Custom class ID for fire
                class_name="🔥 FIRE",
                confidence=confidence,
                bbox=[x/width, y/height, (x+w)/width, (y+h)/height],
                bbox_pixels=[x, y, x+w, y+h]
            ))
        
        return fire_detections
    
    def detect_from_video(
        self,
        video_path: str,
        timestamp: float,
        confidence_threshold: float = 0.3
    ) -> DetectionResult:
        """
        Detect objects at a specific timestamp in a video.
        
        Args:
            video_path: Path to video file
            timestamp: Time in seconds
            confidence_threshold: Minimum confidence
            
        Returns:
            DetectionResult
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_num = int(timestamp * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return DetectionResult(
                detections=[],
                frame_width=0,
                frame_height=0,
                inference_time_ms=0
            )
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return self.detect(frame_rgb, confidence_threshold)


# Test if run directly
if __name__ == "__main__":
    print("Testing object detector...")
    detector = ObjectDetector()
    
    # Create test image
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    result = detector.detect(test_frame)
    print(f"Found {len(result.detections)} objects in {result.inference_time_ms:.1f}ms")
