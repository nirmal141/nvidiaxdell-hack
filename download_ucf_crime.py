"""Download UCF Crime Dataset from Kaggle."""
import kagglehub
import os
import shutil
from pathlib import Path

def download_ucf_crime_dataset(target_dir: str = None):
    """
    Download the UCF Crime dataset from Kaggle.
    
    Args:
        target_dir: Optional target directory. If None, uses default kaggle cache.
    
    Returns:
        Path to the downloaded dataset.
    """
    print("Downloading UCF Crime Dataset from Kaggle...")
    print("This may take a while (dataset is ~13GB)...")
    
    # Download the dataset
    path = kagglehub.dataset_download("odins0n/ucf-crime-dataset")
    
    print(f"\n✅ Dataset downloaded to: {path}")
    
    # List contents
    print("\nDataset contents:")
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            count = len(os.listdir(item_path))
            print(f"  📁 {item}/ ({count} items)")
        else:
            size = os.path.getsize(item_path) / (1024 * 1024)
            print(f"  📄 {item} ({size:.1f} MB)")
    
    # Optionally copy some samples to the app's video directory
    if target_dir:
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        print(f"\nTo copy videos to your app, run:")
        print(f"  cp {path}/<category>/<video>.mp4 {target_dir}/")
    
    return path


def copy_sample_videos(source_path: str, target_dir: str, max_per_category: int = 2):
    """
    Copy a few sample videos from each category to the target directory.
    
    Args:
        source_path: Path to the downloaded UCF Crime dataset
        target_dir: Target directory (e.g., data/videos)
        max_per_category: Maximum videos to copy per category
    """
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    for category in os.listdir(source_path):
        category_path = os.path.join(source_path, category)
        if not os.path.isdir(category_path):
            continue
        
        videos = [f for f in os.listdir(category_path) if f.endswith(('.mp4', '.avi'))]
        for video in videos[:max_per_category]:
            src = os.path.join(category_path, video)
            # Prefix with category name for clarity
            dst = target_path / f"{category}_{video}"
            if not dst.exists():
                print(f"Copying: {category}/{video}")
                shutil.copy2(src, dst)
                copied += 1
    
    print(f"\n✅ Copied {copied} sample videos to {target_dir}")


if __name__ == "__main__":
    # Download the dataset
    dataset_path = download_ucf_crime_dataset()
    
    # Optionally copy samples to app's video directory
    # Uncomment the following lines to copy 2 videos from each category:
    # copy_sample_videos(
    #     source_path=dataset_path,
    #     target_dir="./data/videos",
    #     max_per_category=2
    # )
