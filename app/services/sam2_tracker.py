"""SAM2 segmentation and tracking service."""
import torch
import numpy as np
from typing import Optional, List, Tuple
import logging
import cv2
from dataclasses import dataclass
from PIL import Image

logger = logging.getLogger(__name__)

# SAM2 model path
MODEL_PATH = "/models/models--facebook--sam2-hiera-large"


@dataclass
class SegmentationResult:
    """Result of SAM2 segmentation."""
    mask: np.ndarray  # Binary mask (H, W)
    polygon: List[List[float]]  # Polygon points for rendering
    area: float  # Mask area as percentage
    confidence: float


class SAM2Tracker:
    """SAM2-based object segmentation and tracking."""
    
    _instance: Optional['SAM2Tracker'] = None
    _model = None
    _processor = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the tracker."""
        if SAM2Tracker._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load SAM2 model."""
        try:
            from transformers import Sam2Processor, Sam2Model
            
            logger.info("Loading SAM2-hiera-large model...")
            
            SAM2Tracker._processor = Sam2Processor.from_pretrained(
                "facebook/sam2-hiera-large",
                cache_dir="/models"
            )
            
            SAM2Tracker._model = Sam2Model.from_pretrained(
                "facebook/sam2-hiera-large",
                cache_dir="/models",
                torch_dtype=torch.float16
            )
            
            if torch.cuda.is_available():
                SAM2Tracker._model = SAM2Tracker._model.to("cuda")
                logger.info("SAM2 loaded on GPU")
            else:
                logger.info("SAM2 loaded on CPU")
                
        except ImportError:
            logger.warning("SAM2 not available, using fallback segmentation")
            SAM2Tracker._model = "fallback"
    
    def segment_point(
        self, 
        frame: np.ndarray, 
        x: float, 
        y: float
    ) -> SegmentationResult:
        """
        Segment object at the given point.
        
        Args:
            frame: RGB numpy array (H, W, 3)
            x: X coordinate (0-1 normalized)
            y: Y coordinate (0-1 normalized)
            
        Returns:
            SegmentationResult with mask and polygon
        """
        height, width = frame.shape[:2]
        
        # Convert normalized coords to pixels
        px = int(x * width)
        py = int(y * height)
        
        if SAM2Tracker._model == "fallback":
            # Fallback: Use color-based segmentation around click point
            return self._fallback_segment(frame, px, py)
        
        try:
            # Prepare image for SAM2
            pil_image = Image.fromarray(frame)
            
            # Process with SAM2
            inputs = self._processor(
                images=pil_image,
                input_points=[[[px, py]]],
                return_tensors="pt"
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") if hasattr(v, 'to') else v for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self._model(**inputs)
            
            # Get mask
            masks = self._processor.post_process_masks(
                outputs.pred_masks,
                inputs["original_sizes"],
                inputs["reshaped_input_sizes"]
            )
            
            mask = masks[0][0][0].cpu().numpy()  # Best mask
            
        except Exception as e:
            logger.warning(f"SAM2 segmentation failed: {e}, using fallback")
            return self._fallback_segment(frame, px, py)
        
        # Convert mask to polygon
        polygon = self._mask_to_polygon(mask)
        area = np.sum(mask) / (height * width) * 100
        
        return SegmentationResult(
            mask=mask,
            polygon=polygon,
            area=area,
            confidence=0.9
        )
    
    def _fallback_segment(
        self, 
        frame: np.ndarray, 
        px: int, 
        py: int
    ) -> SegmentationResult:
        """
        Fallback segmentation using GrabCut algorithm.
        Used when SAM2 is not available.
        """
        height, width = frame.shape[:2]
        
        # Create initial rectangle around click point
        rect_size = min(width, height) // 4
        x1 = max(0, px - rect_size)
        y1 = max(0, py - rect_size)
        x2 = min(width, px + rect_size)
        y2 = min(height, py + rect_size)
        
        # GrabCut segmentation
        mask = np.zeros((height, width), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        rect = (x1, y1, x2 - x1, y2 - y1)
        
        try:
            cv2.grabCut(frame, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
            mask = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        except:
            # If GrabCut fails, just use the rectangle
            mask = np.zeros((height, width), dtype=np.uint8)
            mask[y1:y2, x1:x2] = 1
        
        polygon = self._mask_to_polygon(mask)
        area = np.sum(mask) / (height * width) * 100
        
        return SegmentationResult(
            mask=mask,
            polygon=polygon,
            area=area,
            confidence=0.6
        )
    
    def _mask_to_polygon(self, mask: np.ndarray) -> List[List[float]]:
        """Convert binary mask to polygon points."""
        # Find contours
        contours, _ = cv2.findContours(
            mask.astype(np.uint8), 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        if not contours:
            return []
        
        # Get largest contour
        largest = max(contours, key=cv2.contourArea)
        
        # Simplify polygon
        epsilon = 0.005 * cv2.arcLength(largest, True)
        approx = cv2.approxPolyDP(largest, epsilon, True)
        
        # Convert to list of [x, y] normalized points
        height, width = mask.shape
        polygon = []
        for point in approx:
            x = float(point[0][0]) / width
            y = float(point[0][1]) / height
            polygon.append([x, y])
        
        return polygon
    
    def segment_from_video(
        self,
        video_path: str,
        timestamp: float,
        x: float,
        y: float
    ) -> SegmentationResult:
        """
        Segment object at point in a video frame.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_num = int(timestamp * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return SegmentationResult(
                mask=np.zeros((1, 1), dtype=np.uint8),
                polygon=[],
                area=0,
                confidence=0
            )
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return self.segment_point(frame_rgb, x, y)


# Test if run directly
if __name__ == "__main__":
    print("Testing SAM2 tracker...")
    tracker = SAM2Tracker()
    
    # Create test image
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    result = tracker.segment_point(test_frame, 0.5, 0.5)
    print(f"Segmented area: {result.area:.1f}%, polygon points: {len(result.polygon)}")
