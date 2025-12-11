"""Local VLM inference service using LLaVA on GPU."""
import torch
from transformers import AutoProcessor, LlavaForConditionalGeneration
from PIL import Image
import numpy as np
from typing import Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MODEL_ID = "llava-hf/llava-1.5-7b-hf"
CACHE_DIR = "/models"


@dataclass
class VLMResponse:
    """Response from local VLM."""
    description: str
    raw_response: dict


class LocalVLMClient:
    """Local VLM client using LLaVA on GPU."""
    
    _instance: Optional['LocalVLMClient'] = None
    _model = None
    _processor = None
    
    def __new__(cls):
        """Singleton pattern to avoid loading model multiple times."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the local VLM client."""
        if LocalVLMClient._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load the LLaVA model."""
        logger.info(f"Loading LLaVA model from {CACHE_DIR}...")
        
        # Load processor
        LocalVLMClient._processor = AutoProcessor.from_pretrained(
            MODEL_ID,
            cache_dir=CACHE_DIR,
            trust_remote_code=True
        )
        
        # Load model on GPU
        LocalVLMClient._model = LlavaForConditionalGeneration.from_pretrained(
            MODEL_ID,
            cache_dir=CACHE_DIR,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        logger.info(f"LLaVA loaded on {next(LocalVLMClient._model.parameters()).device}")
    
    def describe_frame(self, image: np.ndarray) -> VLMResponse:
        """
        Generate a description of a video frame.
        
        Args:
            image: RGB numpy array of the frame
            
        Returns:
            VLMResponse with description
        """
        # Convert numpy to PIL
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # LLaVA-1.5 conversation format - incident/emergency focused
        surveillance_prompt = """Analyze this surveillance/CCTV frame for INCIDENTS and ANOMALIES.

CRITICAL - Look for:
- People lying on ground (accident/injury/attack)
- Fallen motorcycles or crashed vehicles
- People running or fleeing
- Fighting or aggressive behavior
- Fire, smoke, or explosions
- Crowd gathering around an incident
- Unusual body positions (collapsed, injured)

Describe what you see in 2-3 sentences:
1. Any INCIDENT or EMERGENCY (accidents, falls, attacks, fires)
2. People: count, actions, and any distress signals
3. Vehicles: any damage, crashes, or unusual positions

Be SPECIFIC about incidents. Do NOT describe as "normal" if there's anything unusual."""

        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": surveillance_prompt}
                ]
            }
        ]
        
        # Apply chat template
        prompt = self._processor.apply_chat_template(conversation, add_generation_prompt=True)
        
        # Prepare inputs
        inputs = self._processor(
            text=prompt,
            images=pil_image,
            return_tensors="pt"
        ).to(self._model.device)
        
        # Generate
        with torch.no_grad():
            output = self._model.generate(
                **inputs,
                max_new_tokens=150,
                do_sample=False
            )
        
        # Decode - get only the new tokens
        generated_ids = output[0][inputs['input_ids'].shape[1]:]
        description = self._processor.decode(generated_ids, skip_special_tokens=True).strip()
        
        # Fallback if empty
        if not description:
            description = "Frame shows a scene with various elements."
        
        logger.debug(f"Generated description: {description[:100]}...")
        
        return VLMResponse(
            description=description,
            raw_response={"text": description}
        )


# Test if run directly
if __name__ == "__main__":
    import cv2
    
    print("Testing local VLM...")
    client = LocalVLMClient()
    
    # Create a test image
    test_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    print("Running inference...")
    result = client.describe_frame(test_image)
    print(f"Result: {result.description}")
