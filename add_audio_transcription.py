"""Add audio transcription to already-processed videos."""
import json
import asyncio
from pathlib import Path

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from app.services.audio_transcriber import get_audio_transcriber, WHISPER_AVAILABLE
from app.services.nim_client import NIMClientFactory
from app.services.vector_store import VectorStore
from app.config import config

VIDEOS_DIR = Path("./data/videos")
METADATA_FILE = VIDEOS_DIR / "videos_metadata.json"


async def transcribe_video(video_id: str, video_path: str, vector_store: VectorStore, embedding_client):
    """Add audio transcription to a video."""
    print(f"\n📢 Transcribing audio for: {video_id}")
    
    transcriber = get_audio_transcriber()
    segments = transcriber.transcribe_segments(video_path, segment_duration=10.0)
    
    if not segments:
        print(f"  ⚠️ No audio segments found")
        return 0
    
    print(f"  Found {len(segments)} audio segments")
    
    # Embed and store
    audio_descriptions = []
    for seg in segments:
        if not seg.text.strip():
            continue
        
        description = f"[AUDIO] {seg.text}"
        
        try:
            embed_response = embedding_client.embed_text(description)
            audio_descriptions.append({
                "timestamp": seg.start,
                "description": description,
                "embedding": embed_response.embedding
            })
        except Exception as e:
            print(f"  ⚠️ Embedding error: {e}")
            continue
    
    if audio_descriptions:
        vector_store.insert_descriptions(video_id, audio_descriptions)
        print(f"  ✅ Added {len(audio_descriptions)} audio segments")
    
    return len(audio_descriptions)


async def main():
    if not WHISPER_AVAILABLE:
        print("❌ faster-whisper not installed. Run: pip install faster-whisper")
        return
    
    # Load metadata
    if not METADATA_FILE.exists():
        print("❌ No videos metadata found")
        return
    
    with open(METADATA_FILE) as f:
        metadata = json.load(f)
    
    # Filter completed videos
    completed = [(vid, info) for vid, info in metadata.items() 
                 if info.get("status") == "completed"]
    
    if not completed:
        print("❌ No completed videos found")
        return
    
    print(f"Found {len(completed)} completed videos")
    
    # Initialize services - use same config as main app
    if config.video.use_local_embedding:
        from app.services.local_embedding import LocalEmbeddingClient
        embedding_client = LocalEmbeddingClient()
        print("Using LOCAL embeddings (384-dim)")
    else:
        embedding_client = NIMClientFactory.create_embedding_client(config)
        print("Using CLOUD embeddings (1024-dim)")
    
    vector_store = VectorStore(
        db_path=config.milvus.db_path,
        collection_name=config.milvus.collection_name,
        embedding_dim=config.milvus.embedding_dim
    )
    
    total_segments = 0
    for video_id, info in completed:
        path = info.get("path")
        if not path:
            print(f"⚠️ No path for: {video_id}")
            continue
        
        # Handle Docker path mapping
        video_path = Path(path)
        if not video_path.exists():
            # Try /workspace prefix (Docker mount)
            alt_path = Path("/workspace/data/videos") / video_path.name
            if alt_path.exists():
                video_path = alt_path
            else:
                # Try relative to current dir
                alt_path = VIDEOS_DIR / video_path.name
                if alt_path.exists():
                    video_path = alt_path
                else:
                    print(f"⚠️ Video file not found: {video_id} ({path})")
                    continue
        
        count = await transcribe_video(video_id, str(video_path), vector_store, embedding_client)
        total_segments += count
    
    print(f"\n✅ Done! Added {total_segments} total audio segments")


if __name__ == "__main__":
    asyncio.run(main())
