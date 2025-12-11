# Sentio

> **Visual RAG for Security & Law Enforcement** — An AI-powered video intelligence platform that transforms raw surveillance footage into searchable, queryable knowledge.

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![NVIDIA](https://img.shields.io/badge/NVIDIA-NIM%20%2B%20Local%20GPU-76B900)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 What is Sentio?

Sentio is a **Visual Retrieval-Augmented Generation (RAG)** system designed for security and law enforcement applications. It processes video footage (body cams, surveillance, dashcams) and enables natural language search across:

- **Visual content** — What's happening in frames
- **Spoken audio** — What people are saying (transcribed with timestamps)
- **Detected objects** — People, vehicles, fire, weapons

### Key Differentiators

| Traditional Approach | Sentio Approach |
|---------------------|-----------------|
| Manual video review | AI-powered semantic search |
| Keyword-based search | Natural language queries |
| Single video at a time | Cross-video intelligence |
| Visual only | Visual + Audio fusion |
| Cloud-dependent | Hybrid Cloud + Local GPU |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              SENTIO PLATFORM                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────┐ │
│  │   React     │───▶│                 FastAPI Backend                  │ │
│  │   Frontend  │    │  ┌─────────────────────────────────────────────┐ │ │
│  │             │◀───│  │            Video Processing Pipeline        │ │ │
│  └─────────────┘    │  │  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │ │ │
│                     │  │  │  Frame  │  │  Audio  │  │   Object    │  │ │ │
│                     │  │  │  VLM    │  │ Whisper │  │  Detection  │  │ │ │
│                     │  │  └────┬────┘  └────┬────┘  └──────┬──────┘  │ │ │
│                     │  └───────┴────────────┴─────────────┴──────────┘ │ │
│                     │                       │                          │ │
│                     │  ┌────────────────────▼─────────────────────────┐│ │
│                     │  │           Embedding + Vector Store           ││ │
│                     │  │  ┌─────────────┐    ┌─────────────────────┐  ││ │
│                     │  │  │  NV-Embed   │    │    Milvus Lite      │  ││ │
│                     │  │  │  (384-dim)  │───▶│  (Local Vector DB)  │  ││ │
│                     │  │  └─────────────┘    └─────────────────────┘  ││ │
│                     │  └──────────────────────────────────────────────┘│ │
│                     └─────────────────────────────────────────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                         AI Model Stack                               ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  ││
│  │  │ LLaVA 1.5 7B    │  │ Whisper Base    │  │ YOLOv8x + SAM2      │  ││
│  │  │ (Local GPU VLM) │  │ (Audio→Text)    │  │ (Detection+Segment) │  ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘  ││
│  │  ┌─────────────────────────────────────────────────────────────────┐││
│  │  │              NVIDIA NIM Cloud (Fallback / Answer Gen)           │││
│  │  │    Llama 3.2 90B Vision  │  Llama 3.1 70B  │  NV-EmbedQA E5 V5  │││
│  │  └─────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Core AI Models

| Component | Model | Why This Choice |
|-----------|-------|-----------------|
| **Vision-Language** | LLaVA 1.5 7B (Local) | Fast local inference, good quality descriptions, runs on 8GB VRAM |
| **Audio Transcription** | Whisper Base (faster-whisper) | Best OSS speech recognition, word-level timestamps, VAD filtering |
| **Object Detection** | YOLOv8x | State-of-the-art detection, 80+ classes, real-time on GPU |
| **Segmentation** | SAM2 (Segment Anything 2) | Click-to-track any object, zero-shot segmentation |
| **Embeddings** | Sentence-Transformers (Local) | 384-dim vectors, fast local embedding |
| **Answer Generation** | Llama 3.1 70B (NIM Cloud) | High-quality reasoning with context |

### Why Local + Cloud Hybrid?

```
┌─────────────────────────────────────────────────────────────────┐
│                    COST & LATENCY OPTIMIZATION                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LOCAL GPU (Most Operations)         CLOUD API (When Needed)   │
│  ├── Frame descriptions (LLaVA)      ├── Complex Q&A (Llama)  │
│  ├── Audio transcription (Whisper)   └── High-stakes analysis │
│  ├── Object detection (YOLO)                                   │
│  ├── Segmentation (SAM2)                                       │
│  └── Embeddings (sentence-transformers)                        │
│                                                                 │
│  💰 Cost: $0 per frame              💰 Cost: ~$0.001 per query │
│  ⚡ Latency: ~200ms                 ⚡ Latency: ~2-3s           │
└─────────────────────────────────────────────────────────────────┘
```

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI | Async REST API + WebSocket for real-time updates |
| **Frontend** | React + Tailwind | Modern dashboard with database-style video library |
| **Vector DB** | Milvus Lite | Embedded vector search, no external dependencies |
| **Video Processing** | OpenCV + CUDA | GPU-accelerated frame extraction |
| **GPU Runtime** | NVIDIA NGC Container | Pre-configured PyTorch + CUDA environment |

---

## ✨ Key Features

### 1. Multi-Modal Search
Search across **visual content** AND **spoken audio** simultaneously.

```
Query: "when did the officer mention license"
└── Searches both frame descriptions AND audio transcriptions
    └── Returns: [AUDIO] "License and registration please" @ 01:23
```

### 2. Smart Deduplication
Results are grouped by **30-second windows** — no more seeing 20 nearly-identical frames.

```
Before: Frame@1:14, Frame@1:15, Frame@1:16, Frame@1:17...
After:  Best match from 1:00-1:30 window, Best match from 1:30-2:00 window...
```

### 3. Real-Time Object Detection
Click "Detect" to identify all objects in current frame:
- People count
- Vehicle detection (cars, trucks, motorcycles)
- Fire detection (custom color analysis)
- Weapons, bags, electronics

### 4. Click-to-Track (SAM2)
Click on any object → AI segments and tracks it across frames.

### 5. AI-Powered Summaries
Every search returns an AI analysis synthesizing findings across videos:

```
"There are multiple car accidents in the footage. In [Florida Man] at [02:16], 
a car has crashed into a tree. In the same video at [01:14], a person is lying 
on the ground nearby..."
```

---

## 📁 Project Structure

```
nirmal-hackathon/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration management
│   ├── api/
│   │   └── routes.py              # All REST + WebSocket endpoints
│   ├── services/
│   │   ├── qa_service.py          # Core Q&A orchestration
│   │   ├── video_processor.py     # Frame extraction + thumbnails
│   │   ├── vector_store.py        # Milvus vector operations
│   │   ├── local_vlm.py           # LLaVA local inference
│   │   ├── local_embedding.py     # Sentence-transformers embeddings
│   │   ├── audio_transcriber.py   # Whisper transcription
│   │   ├── object_detector.py     # YOLO + fire detection
│   │   ├── sam2_tracker.py        # Click-to-segment
│   │   └── nim_client.py          # NVIDIA NIM Cloud APIs
│   └── models/
│       └── schemas.py             # Pydantic models
├── frontend/
│   └── src/
│       ├── App.tsx                # Main application
│       ├── components/
│       │   ├── Dashboard.tsx      # Database-style video library
│       │   ├── VideoPlayer.tsx    # Video + detection overlay
│       │   ├── Chat.tsx           # Q&A interface
│       │   └── Sidebar.tsx        # Video list + upload
│       └── api.ts                 # API client
├── data/
│   ├── videos/                    # Uploaded videos + metadata
│   └── milvus/                    # Vector database files
├── requirements.txt               # Python dependencies
├── run.py                         # Development server
└── register_videos.py             # Bulk video registration
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- NVIDIA GPU (8GB+ VRAM recommended)
- Docker (for GPU container)
- NVIDIA API key from [build.nvidia.com](https://build.nvidia.com)

### Option 1: Docker (Recommended)

```bash
# Run NVIDIA container with GPU
docker run --gpus all -it --rm \
  -v $(pwd):/workspace \
  -v ~/hf-models:/models \
  -p 8080:8080 \
  -w /workspace \
  nvcr.io/nvidia/pytorch:25.11-py3

# Inside container
pip install -r requirements.txt
pip install faster-whisper
apt-get update && apt-get install -y ffmpeg
echo "NVIDIA_API_KEY=nvapi-xxx" > .env
python run.py
```

### Option 2: Local venv

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "NVIDIA_API_KEY=nvapi-xxx" > .env
python run.py
```

### Access
Open [http://localhost:8080](http://localhost:8080)

---

## 📋 API Reference

### Video Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/videos` | List all videos |
| `POST` | `/api/videos/upload` | Upload video file |
| `DELETE` | `/api/videos/{id}` | Delete video + data |
| `GET` | `/api/videos/{id}/stream` | Stream video |
| `GET` | `/api/videos/{id}/thumbnail` | Get thumbnail |

### AI Processing
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/videos/{id}/process` | Start AI analysis |
| `POST` | `/api/videos/{id}/stop` | Stop processing |
| `GET` | `/api/videos/{id}/status` | Get progress |
| `WS` | `/ws/progress/{id}` | Real-time progress |

### Search & Q&A
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/search` | Global semantic search |
| `POST` | `/api/videos/{id}/ask` | Ask question about video |

### Detection & Tracking
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/videos/{id}/detect` | Detect objects at timestamp |
| `POST` | `/api/videos/{id}/segment` | Segment object at click point |

---

## 🔧 Configuration

### Environment Variables

```bash
NVIDIA_API_KEY=nvapi-xxx          # Required for cloud LLM
CACHE_DIR=/models                  # Model cache directory
WHISPER_MODEL=base                 # tiny/base/small/medium
```

### Config Options (`app/config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `use_local_vlm` | `True` | Use local LLaVA vs cloud |
| `use_local_embedding` | `True` | Use local embeddings vs cloud |
| `frame_sample_interval` | `1.0` | Seconds between frame samples |
| `embedding_dim` | `384` | Vector dimension (384 local, 1024 cloud) |

---

## 📊 Why Sentio is Better

### vs. Traditional Video Search
| Aspect | Traditional | Sentio |
|--------|-------------|--------|
| Search method | Keyword/metadata | Semantic understanding |
| Audio | Ignored | Transcribed + searchable |
| Cross-video | Manual | Automatic |
| Evidence linking | Manual | AI-assisted with timestamps |

### vs. Cloud-Only Solutions
| Aspect | Cloud-Only | Sentio |
|--------|------------|--------|
| Cost per video | $1-10 | ~$0.10 (mostly local) |
| Data privacy | Leaves device | Stays local |
| Latency | 2-3s/frame | ~200ms/frame |
| Offline support | None | Full (except Q&A) |

### vs. Basic Vision AI
| Aspect | Basic Vision | Sentio |
|--------|--------------|--------|
| Audio | ❌ | ✅ Whisper transcription |
| Object tracking | ❌ | ✅ SAM2 click-to-track |
| Temporal context | ❌ | ✅ 30s window deduplication |
| Answer generation | ❌ | ✅ LLM with sources |

---

## 🔒 Security & Privacy

- **Local-first processing** — Video analysis runs on your GPU
- **No cloud upload** — Only text queries go to cloud API (optionally)
- **Air-gap capable** — Can run fully offline with local models
- **Evidence integrity** — Original files never modified

---

## 📝 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **NVIDIA** — NIM Cloud APIs, NGC Containers
- **Meta** — LLaVA, Llama, SAM2 models
- **OpenAI** — Whisper architecture
- **Ultralytics** — YOLOv8
- **Milvus** — Vector database
- **FastAPI** — Web framework

---

<div align="center">

**Built for the NVIDIA AI Hackathon 2024**

[Demo](http://localhost:8080) · [Report Bug](https://github.com/yourrepo/issues) · [Request Feature](https://github.com/yourrepo/issues)

</div>
