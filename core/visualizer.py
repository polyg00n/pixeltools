"""
core/visualizer.py

Generates side-by-side or grid comparisons of AOVs from a single EXR file.
Useful for visual inspection of different render passes.
"""

import os
import logging
import numpy as np
import imageio.v3 as iio
from pathlib import Path
from typing import List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_aov_comparison(exr_path, aovs=None, out_name=None):
    """
    Generates a single image showing selected AOVs from one EXR file.

    Parameters:
        exr_path: Path to an EXR file
        aovs: List of AOV base names (e.g., ['diffcol', 'depth'])
        out_name: Optional name for saved PNG file
    """
    exr_path = Path(exr_path)
    if aovs is None:
        aovs = get_exr_aovs(exr_path)

    tiles = []
    for aov in aovs:
        # Load AOV using image_loader
        aov_data = load_image(exr_path, aov)
        if aov_data is not None:
            # Normalize to 0-1 range
            if aov_data.max() > aov_data.min():
                aov_data = (aov_data - aov_data.min()) / (aov_data.max() - aov_data.min())
            
            # Convert to RGB
            if len(aov_data.shape) == 2:
                aov_data = np.stack([aov_data] * 3, axis=-1)
            
            # Add label
            tile = add_text_to_image(aov_data.copy(), aov)
            tiles.append(tile)

    if not tiles:
        print("No valid AOVs found to display.")
        return

    height = max(tile.shape[0] for tile in tiles)
    padded = []
    for img in tiles:
        # Create padding
        pad_height = height - img.shape[0]
        if pad_height > 0:
            padded_img = np.pad(img, ((0, pad_height), (0, 0), (0, 0)), mode='constant')
        else:
            padded_img = img
        padded.append(padded_img)
    
    out = np.hstack(padded)

    if out_name is None:
        out_name = exr_path.with_name(exr_path.stem + "_aov_grid.png")

    iio.imwrite(str(out_name), out)
    print(f"Saved AOV comparison to: {out_name}")

def add_text_to_image(img, text):
    """Add text to image using PIL."""
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    
    # Convert numpy array to PIL Image
    pil_img = Image.fromarray((img * 255).astype(np.uint8))
    draw = ImageDraw.Draw(pil_img)
    
    # Use default font
    font = ImageFont.load_default()
    
    # Add text
    draw.text((10, 10), text, fill=(255, 255, 255), font=font)
    
    # Convert back to numpy array
    return np.array(pil_img) / 255.0

def create_thumbnail_grid(
    image_paths: List[str],
    output_path: str,
    grid_size: Optional[Tuple[int, int]] = None,
    max_size: Optional[Tuple[int, int]] = None
) -> bool:
    """
    Create a grid of thumbnails from multiple images.
    
    Args:
        image_paths: List of paths to input images
        output_path: Path to save the grid image
        grid_size: Optional (rows, cols) for the grid
        max_size: Optional maximum dimensions for each thumbnail
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not image_paths:
            logger.error("No images provided")
            return False
            
        # Load all images
        images = []
        for path in image_paths:
            try:
                img = iio.imread(path)
                images.append(img)
            except Exception as e:
                logger.error(f"Error loading image {path}: {str(e)}")
                continue
                
        if not images:
            logger.error("No images could be loaded")
            return False
            
        # Get dimensions of first image
        height, width = images[0].shape[:2]
        
        # Calculate grid size if not provided
        if grid_size is None:
            n = len(images)
            cols = int(np.ceil(np.sqrt(n)))
            rows = int(np.ceil(n / cols))
        else:
            rows, cols = grid_size
            
        # Calculate thumbnail size
        if max_size:
            thumb_width = min(width, max_size[0])
            thumb_height = min(height, max_size[1])
        else:
            thumb_width = width
            thumb_height = height
            
        # Create grid
        grid = np.zeros((thumb_height * rows, thumb_width * cols, 3), dtype=np.uint8)
        
        # Fill grid
        for i, img in enumerate(images):
            if i >= rows * cols:
                break
                
            # Calculate position
            row = i // cols
            col = i % cols
            
            # Resize image if needed
            if img.shape[:2] != (thumb_height, thumb_width):
                img = iio.imresize(img, (thumb_height, thumb_width))
                
            # Convert to RGB if needed
            if len(img.shape) == 2:
                img = np.stack([img] * 3, axis=-1)
            elif img.shape[2] == 4:
                img = img[..., :3]
                
            # Convert to 8-bit if needed
            if img.dtype != np.uint8:
                if img.max() > 1.0:
                    img = img / img.max()
                img = (img * 255).astype(np.uint8)
                
            # Place in grid
            grid[row*thumb_height:(row+1)*thumb_height, 
                 col*thumb_width:(col+1)*thumb_width] = img
                 
        # Save grid
        iio.imwrite(output_path, grid)
        logger.info(f"Thumbnail grid saved to: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating thumbnail grid: {str(e)}")
        return False

def create_sequence_preview(
    sequence_dir: str,
    output_path: str,
    num_frames: int = 16,
    max_size: Optional[Tuple[int, int]] = None
) -> bool:
    """
    Create a preview image from a sequence by sampling frames.
    
    Args:
        sequence_dir: Directory containing the image sequence
        output_path: Path to save the preview image
        num_frames: Number of frames to sample
        max_size: Optional maximum dimensions for each frame
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        sequence_dir = Path(sequence_dir)
        if not sequence_dir.exists():
            logger.error(f"Sequence directory not found: {sequence_dir}")
            return False
            
        # Get all image files
        image_files = []
        for ext in ['.tiff', '.tif', '.png', '.jpg', '.jpeg']:
            image_files.extend(list(sequence_dir.glob(f'*{ext}')))
            
        if not image_files:
            logger.error(f"No image files found in {sequence_dir}")
            return False
            
        # Sort files by name
        image_files.sort()
        
        # Sample frames evenly
        if len(image_files) <= num_frames:
            sampled_files = image_files
        else:
            indices = np.linspace(0, len(image_files)-1, num_frames, dtype=int)
            sampled_files = [image_files[i] for i in indices]
            
        # Create thumbnail grid
        return create_thumbnail_grid(
            [str(f) for f in sampled_files],
            output_path,
            grid_size=(4, 4),
            max_size=max_size
        )
        
    except Exception as e:
        logger.error(f"Error creating sequence preview: {str(e)}")
        return False
