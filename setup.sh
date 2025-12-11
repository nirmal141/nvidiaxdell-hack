#!/bin/bash
# Startup script for Sentio in Docker

echo "🚀 Installing dependencies..."
pip install -q opencv-python-headless pymilvus milvus-lite python-dotenv aiofiles

echo "✅ Dependencies installed!"
echo ""
echo "Run one of these commands:"
echo "  python run.py          # Start the web server"
echo "  python download_vlm.py # Download local VLM model"
