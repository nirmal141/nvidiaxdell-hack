import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Path to the local model snapshot
model_path = "/models/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-32B/snapshots/711ad2ea6aa40cfca18895e8aca02ab92df1a746"

print(f"Loading model from {model_path}...")

try:
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    print("Model loaded successfully!")
    
    # test generation
    prompt = "Hello, tell me about somthing random."
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    print("Generating response...")
    outputs = model.generate(**inputs, max_new_tokens=50)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    print("\n--- Response ---")
    print(response)
    print("----------------")

except Exception as e:
    print(f"Error loading model: {e}")
