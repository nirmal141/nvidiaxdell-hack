"""Download and setup local VLM for GPU inference."""
import torch
from transformers import AutoProcessor, LlavaForConditionalGeneration
import os

MODEL_ID = "llava-hf/llava-1.5-7b-hf"
CACHE_DIR = "/models"

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

print(f"\nDownloading {MODEL_ID}...")
print("This may take 10-15 minutes for the first download (~15GB)")

# Download processor
print("\n[1/2] Downloading processor...")
processor = AutoProcessor.from_pretrained(
    MODEL_ID, 
    cache_dir=CACHE_DIR,
    trust_remote_code=True
)
print("✓ Processor downloaded")

# Download model
print("\n[2/2] Downloading model (this is the large download)...")
model = LlavaForConditionalGeneration.from_pretrained(
    MODEL_ID,
    cache_dir=CACHE_DIR,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
print("✓ Model downloaded and loaded!")

print(f"\nModel loaded on: {next(model.parameters()).device}")
print("\n✅ Setup complete! The local VLM is ready to use.")
