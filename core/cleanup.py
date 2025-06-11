"""
core/cleanup.py

Provides utilities to remove temporary or unnecessary files like generated thumbnails,
intermediate AOV frames, or cache folders.
"""

from pathlib import Path
import shutil

def cleanup_temp_files(root_dir):
    """
    Scans all subdirectories and removes:
    - folders starting with '_aov_'
    - 'preview.mp4' files
    - known temp/cache subfolders like __pycache__, .ipynb_checkpoints, etc.
    """
    root = Path(root_dir)
    if not root.exists():
        print("Invalid folder for cleanup.")
        return

    deleted_items = 0

    for folder in root.rglob("*"):
        if folder.is_dir():
            if folder.name.startswith("_aov_") or folder.name in ["__pycache__", ".ipynb_checkpoints"]:
                shutil.rmtree(folder)
                print(f"Removed folder: {folder}")
                deleted_items += 1

        elif folder.is_file():
            if folder.name == "preview.mp4" or folder.suffix in [".tmp", ".log"]:
                folder.unlink()
                print(f"Removed file: {folder}")
                deleted_items += 1

    print(f"Cleanup complete. Items removed: {deleted_items}")
