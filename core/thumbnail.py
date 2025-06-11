"""
core/thumbnail.py

Creates summary videos for image sequences.
"""

from pathlib import Path
import numpy as np
import imageio.v3 as iio
import logging
from typing import List, Optional, Tuple
from .image_loader import get_sequence_frames, get_sequence_pattern, load_image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_thumbnail_video(
    root_folder: str,
    target_frame: int = 0,
    output_name: str = "thumbnail_summary.mp4",
    max_size: Optional[Tuple[int, int]] = None
) -> bool:
    """
    Creates a summary video where each frame is a tile of the same frame number
    from multiple simulation sequences.

    Args:
        root_folder: Directory containing multiple subfolders with sequences
        target_frame: Frame index to extract (0-based)
        output_name: Output video filename
        max_size: Optional maximum dimensions for each frame (width, height)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        root = Path(root_folder)
        if not root.exists():
            logger.error(f"Root folder not found: {root}")
            return False
            
        # Get all sequence directories
        sims = [d for d in root.iterdir() if d.is_dir() and not d.name.startswith("_")]
        if not sims:
            logger.error(f"No sequence directories found in {root}")
            return False
            
        logger.info(f"Found {len(sims)} sequences")
        
        # Collect frames
        rows = []
        for sim in sims:
            # Get all image files
            image_files = []
            for ext in ['.tiff', '.tif', '.png', '.jpg', '.jpeg']:
                image_files.extend(list(sim.glob(f'*{ext}')))
                
            if not image_files:
                continue
                
            # Sort files by name
            image_files.sort()
            
            if len(image_files) > target_frame:
                # Load frame
                frame = iio.imread(str(image_files[target_frame]))
                
                # Convert to 8-bit if needed
                if frame.dtype != np.uint8:
                    if frame.max() > 1.0:
                        frame = frame / frame.max()
                    frame = (frame * 255).astype(np.uint8)
                    
                # Resize if needed
                if max_size:
                    max_width, max_height = max_size
                    height, width = frame.shape[:2]
                    if width > max_width or height > max_height:
                        scale = min(max_width / width, max_height / height)
                        width = int(width * scale)
                        height = int(height * scale)
                        frame = iio.imresize(frame, (height, width))
                        
                rows.append(frame)
                
        if not rows:
            logger.error("No valid frames found to assemble thumbnail video")
            return False
            
        # Create grid
        height = max(row.shape[0] for row in rows)
        width = max(row.shape[1] for row in rows)
        
        # Create padded rows
        padded_rows = []
        for r in rows:
            pad_height = height - r.shape[0]
            pad_width = width - r.shape[1]
            padded = np.pad(r, ((0, pad_height), (0, pad_width), (0, 0)), mode='constant')
            padded_rows.append(padded)
            
        grid = np.vstack(padded_rows)
        
        # Save grid
        output_path = root / output_name
        iio.imwrite(str(output_path), grid)
        logger.info(f"Thumbnail summary saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating thumbnail video: {str(e)}")
        return False
