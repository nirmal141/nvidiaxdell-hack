# Video Q&A Application

AI-powered video question answering system that allows users to upload videos, process them with AI, and ask natural language questions about the video content.

## 🎯 Overview

This application uses NVIDIA NIM Cloud APIs to:
1. **Analyze video frames** using a Vision-Language Model (VLM)
2. **Create searchable embeddings** of frame descriptions
3. **Answer questions** about video content with timestamp references

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   FastAPI       │────▶│  NVIDIA NIM     │
│   (HTML/JS)     │     │   Backend       │     │  Cloud APIs     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Milvus Lite    │
                        │  Vector DB      │
                        └─────────────────┘
```

## 🛠️ Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | **FastAPI** | REST API and WebSocket support |
| Server | **Uvicorn** | ASGI server with hot reload |
| Video Processing | **OpenCV** | Frame extraction and thumbnails |
| Vector Database | **Milvus Lite** | Store and search embeddings |
| Configuration | **python-dotenv** | Environment variable management |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| UI | **HTML5 + CSS3** | Clean, minimal interface |
| Interactivity | **Vanilla JavaScript** | No framework dependencies |
| Fonts | **Inter (Google Fonts)** | Modern typography |
| Styling | **Custom CSS** | White theme, blue accents |

### AI Models (NVIDIA NIM Cloud API)
| Model | API Endpoint | Purpose |
|-------|--------------|---------|
| **Llama 3.2 90B Vision** | `meta/llama-3.2-90b-vision-instruct` | Describes video frames |
| **NV-EmbedQA E5 V5** | `nvidia/nv-embedqa-e5-v5` | Creates 1024-dim embeddings |
| **Llama 3.1 70B Instruct** | `meta/llama-3.1-70b-instruct` | Generates answers to questions |

## 📁 Project Structure

```
nirmal-hackathon/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Configuration settings
│   ├── api/
│   │   ├── routes.py        # API endpoints
│   │   └── __init__.py
│   ├── services/
│   │   ├── nim_client.py    # NVIDIA NIM API clients
│   │   ├── qa_service.py    # Q&A orchestration
│   │   ├── vector_store.py  # Milvus vector operations
│   │   └── video_processor.py # Video frame extraction
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── static/
│       ├── index.html       # Main UI
│       ├── css/styles.css   # Styling
│       └── js/app.js        # Frontend logic
├── data/
│   ├── videos/              # Uploaded videos
│   └── milvus/              # Vector database
├── .env                     # API keys (not in git)
├── requirements.txt         # Python dependencies
├── run.py                   # Entry point
└── README.md
```

## 🔧 Configuration

### Environment Variables (`.env`)
```bash
NVIDIA_API_KEY=nvapi-xxxxx  # Your NVIDIA NIM API key
```

### Key Settings (`app/config.py`)
| Setting | Default | Description |
|---------|---------|-------------|
| `vlm_model` | `meta/llama-3.2-90b-vision-instruct` | Vision model for frame analysis |
| `embedding_model` | `nvidia/nv-embedqa-e5-v5` | Embedding model (1024 dimensions) |
| `llm_model` | `meta/llama-3.1-70b-instruct` | LLM for answer generation |
| `frame_sample_interval` | `1.0` | Extract 1 frame per second |
| `embedding_dim` | `1024` | Embedding vector dimension |

## 🚀 Running the App

### Prerequisites
- Python 3.12+
- NVIDIA API key from [build.nvidia.com](https://build.nvidia.com)

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
echo "NVIDIA_API_KEY=your-key-here" > .env

# Run the app
python run.py
```

### Access
Open [http://localhost:8080](http://localhost:8080) in your browser.

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/videos` | List all videos |
| `POST` | `/api/videos/upload` | Upload a video |
| `POST` | `/api/videos/{id}/process` | Start AI processing |
| `GET` | `/api/videos/{id}/status` | Get processing status |
| `POST` | `/api/videos/{id}/ask` | Ask a question |
| `GET` | `/api/videos/{id}/stream` | Stream video file |
| `GET` | `/api/videos/{id}/thumbnail` | Get video thumbnail |
| `WS` | `/ws/progress/{id}` | Real-time processing updates |

## 🔄 How It Works

1. **Upload**: User uploads a video file
2. **Process**: 
   - Extract frames at 1 fps
   - Send each frame to VLM for description
   - Generate embeddings for each description
   - Store in Milvus vector database
3. **Query**:
   - User asks a question
   - Embed the question
   - Search for similar frame descriptions
   - Send context to LLM for answer generation
   - Return answer with source timestamps

## 📦 Dependencies

```
fastapi          # Web framework
uvicorn          # ASGI server
python-multipart # File uploads
websockets       # Real-time updates
python-dotenv    # Environment variables
transformers     # Tokenizers
accelerate       # Model utilities
pillow           # Image processing
numpy            # Numerical operations
opencv-python    # Video processing
pymilvus         # Vector database client
milvus-lite      # Local vector database
aiofiles         # Async file operations
pydantic         # Data validation
requests         # HTTP client
```

## 🐳 Docker (GPU Support)

For GPU-accelerated local model inference (optional):

```bash
sudo docker run --gpus all -it --rm \
  -v /path/to/nirmal-hackathon:/workspace \
  -v /path/to/hf-models:/models \
  -w /workspace \
  nvcr.io/nvidia/pytorch:25.11-py3
```

## 📝 License

MIT License

## 🙏 Acknowledgments

- NVIDIA NIM for AI inference APIs
- Milvus for vector search
- FastAPI for the web framework
