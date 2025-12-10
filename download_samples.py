#!/usr/bin/env python3
"""
Download sample videos for testing Video Q&A.

Uses free stock videos from Pexels that represent security/surveillance scenarios.
"""
import os
import urllib.request
import ssl
import sys

# Disable SSL verification for downloads (some CDNs have issues)
ssl._create_default_https_context = ssl._create_unverified_context

# Sample videos directory
SAMPLE_DIR = "./data/sample_videos"

# Free stock videos representing various scenarios
# These are from Pexels (free to use) and represent security-relevant content
SAMPLE_VIDEOS = [
    {
        "name": "traffic_surveillance.mp4",
        "url": "https://videos.pexels.com/video-files/855564/855564-hd_1920_1080_30fps.mp4",
        "category": "Traffic Surveillance",
        "description": "Traffic intersection with vehicles"
    },
    {
        "name": "street_night.mp4",
        "url": "https://videos.pexels.com/video-files/3015510/3015510-hd_1920_1080_24fps.mp4",
        "category": "Night Surveillance",
        "description": "Night time street scene"
    },
    {
        "name": "people_walking.mp4",
        "url": "https://videos.pexels.com/video-files/853889/853889-hd_1920_1080_25fps.mp4",
        "category": "Pedestrian Monitoring",
        "description": "People walking in public area"
    },
    {
        "name": "parking_lot.mp4",
        "url": "https://videos.pexels.com/video-files/857073/857073-hd_1920_1080_25fps.mp4",
        "category": "Parking Surveillance",
        "description": "Parking lot with vehicles"
    },
    {
        "name": "city_intersection.mp4",
        "url": "https://videos.pexels.com/video-files/1448735/1448735-hd_1920_1080_24fps.mp4",
        "category": "City Surveillance",
        "description": "Busy city intersection"
    },
]

def download_video(url, filepath, category):
    """Download a single video file."""
    print(f"📥 Downloading {category}: {os.path.basename(filepath)}...")
    try:
        # Add headers to mimic browser
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=60) as response:
            with open(filepath, 'wb') as out_file:
                out_file.write(response.read())
        
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"   ✅ Downloaded ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def main():
    # Create directory
    os.makedirs(SAMPLE_DIR, exist_ok=True)
    
    print("=" * 60)
    print("🎬 Sample Video Downloader for Video Q&A Testing")
    print("=" * 60)
    print(f"\nDownloading {len(SAMPLE_VIDEOS)} sample videos to: {SAMPLE_DIR}\n")
    
    success_count = 0
    for video in SAMPLE_VIDEOS:
        filepath = os.path.join(SAMPLE_DIR, video["name"])
        
        # Skip if already exists
        if os.path.exists(filepath):
            print(f"⏭️  Skipping {video['name']} (already exists)")
            success_count += 1
            continue
        
        if download_video(video["url"], filepath, video["category"]):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Downloaded {success_count}/{len(SAMPLE_VIDEOS)} videos")
    print(f"📁 Location: {os.path.abspath(SAMPLE_DIR)}")
    print("=" * 60)
    
    # Print categories summary
    print("\n📋 Downloaded Videos:")
    for video in SAMPLE_VIDEOS:
        filepath = os.path.join(SAMPLE_DIR, video["name"])
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"   ✓ {video['name']} ({size_mb:.1f} MB)")
            print(f"     Category: {video['category']}")
            print(f"     Content: {video['description']}")
    
    print("\n🚀 Ready to test!")
    print("   1. Start the app: python run.py")
    print("   2. Open browser: http://localhost:8080")
    print("   3. Upload videos from: data/sample_videos/")

if __name__ == "__main__":
    main()
