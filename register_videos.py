"""Scan videos folder and register all unregistered videos in metadata."""
import os
import json
import uuid
from pathlib import Path
import cv2

VIDEOS_DIR = "/home/dell/Documents/hackathon/nirmal-hackathon/data/videos"
METADATA_FILE = os.path.join(VIDEOS_DIR, "videos_metadata.json")

def get_video_metadata(video_path: str) -> dict:
    """Extract metadata from video file."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    cap.release()
    return {
        "duration": duration,
        "fps": fps,
        "width": width,
        "height": height,
        "total_frames": total_frames
    }

def generate_thumbnail(video_path: str, thumb_path: str):
    """Generate thumbnail from first frame."""
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(thumb_path, frame)
    cap.release()

def main():
    # Load existing metadata
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {}
    
    # Get existing filenames
    registered_files = {v.get("filename") for v in metadata.values()}
    
    # Scan for new videos
    added = 0
    for filename in os.listdir(VIDEOS_DIR):
        if not filename.endswith(('.mp4', '.avi', '.mkv', '.mov')):
            continue
        
        # Skip if already registered
        if filename in registered_files:
            continue
        
        video_path = os.path.join(VIDEOS_DIR, filename)
        if not os.path.isfile(video_path):
            continue
        
        # Generate ID
        video_id = str(uuid.uuid4())[:8]
        
        # Get metadata
        try:
            meta = get_video_metadata(video_path)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue
        
        # Generate thumbnail
        thumb_path = os.path.join(VIDEOS_DIR, f"{video_id}_thumb.jpg")
        generate_thumbnail(video_path, thumb_path)
        
        # Extract name (remove ID prefix if present)
        name = Path(filename).stem
        if '_' in name and len(name.split('_')[0]) == 8:
            name = '_'.join(name.split('_')[1:])
        
        # Register
        metadata[video_id] = {
            "id": video_id,
            "filename": filename,
            "path": video_path,
            "status": "pending",
            "processed_frames": 0,
            "name": name,
            "duration": meta["duration"],
            "fps": meta["fps"],
            "width": meta["width"],
            "height": meta["height"],
            "total_frames": meta["total_frames"],
            "thumbnail": thumb_path
        }
        
        print(f"Registered: {name} ({video_id})")
        added += 1
    
    # Save metadata
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Added {added} videos. Total: {len(metadata)} videos in library.")

if __name__ == "__main__":
    main()
