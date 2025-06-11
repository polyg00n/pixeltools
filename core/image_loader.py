"""
image_loader.py

Handles reading image files (EXR, PNG, JPG), optionally with AOV selection.
Supports returning images as NumPy arrays for further processing.
"""

import os
import logging
import numpy as np
import imageio.v3 as iio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_FORMATS = {
    '.tiff': 'TIFF',
    '.tif': 'TIFF',
    '.png': 'PNG',
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG'
}

def load_image(file_path: str) -> Tuple[np.ndarray, Dict]:
    """
    Load an image file (TIFF, PNG, or JPEG).
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Tuple of (image_data, metadata)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or format not supported
        RuntimeError: If image loading fails
    """
    try:
        file_path = str(Path(file_path).resolve())
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError(f"Empty file: {file_path}")
            
        # Check file format
        ext = Path(file_path).suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {ext}. Supported formats: {', '.join(SUPPORTED_FORMATS.keys())}")
            
        logger.info(f"Loading {SUPPORTED_FORMATS[ext]} image: {file_path}")
        logger.info(f"File size: {file_size / 1024 / 1024:.2f} MB")
        
        # Load the image
        img_data = iio.imread(file_path)
        
        # Log image properties
        logger.info(f"Image shape: {img_data.shape}")
        logger.info(f"Image dtype: {img_data.dtype}")
        logger.info(f"Value range: [{img_data.min()}, {img_data.max()}]")
        
        # Create metadata
        metadata = {
            'format': SUPPORTED_FORMATS[ext],
            'shape': img_data.shape,
            'dtype': str(img_data.dtype),
            'value_range': [float(img_data.min()), float(img_data.max())]
        }
        
        return img_data, metadata
            
    except Exception as e:
        logger.error(f"Error loading image {file_path}: {str(e)}")
        raise

def get_sequence_frames(sequence_dir: str) -> List[str]:
    """
    Get all image frames in a sequence directory.
    
    Args:
        sequence_dir: Path to the sequence directory
        
    Returns:
        List of frame file paths
        
    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    try:
        sequence_dir = Path(sequence_dir)
        if not sequence_dir.exists():
            raise FileNotFoundError(f"Sequence directory not found: {sequence_dir}")
            
        # Get all supported image files
        image_files = []
        for ext in SUPPORTED_FORMATS.keys():
            image_files.extend(list(sequence_dir.glob(f'*{ext}')))
            
        # Sort files by name
        image_files.sort()
        
        if not image_files:
            logger.warning(f"No supported image files found in {sequence_dir}")
            return []
            
        logger.info(f"Found {len(image_files)} image files in {sequence_dir}")
        return [str(f) for f in image_files]
        
    except Exception as e:
        logger.error(f"Error getting sequence frames from {sequence_dir}: {str(e)}")
        raise

def get_sequence_pattern(sequence_dir: str) -> str:
    """
    Get the pattern for a sequence of images.
    
    Args:
        sequence_dir: Path to the sequence directory
        
    Returns:
        Pattern string (e.g., "frame_%04d.png")
    """
    try:
        frames = get_sequence_frames(sequence_dir)
        if not frames:
            return ""
            
        # Get the first frame
        first_frame = Path(frames[0])
        
        # Get the extension
        ext = first_frame.suffix
        
        # Get the base name without extension
        base_name = first_frame.stem
        
        # Find the numeric part
        import re
        match = re.search(r'\d+', base_name)
        if match:
            num_str = match.group()
            # Replace the numeric part with %04d
            pattern = base_name.replace(num_str, '%04d') + ext
            return pattern
            
        return ""
        
    except Exception as e:
        logger.error(f"Error getting sequence pattern from {sequence_dir}: {str(e)}")
        return ""

def save_image(file_path: str, image_data: np.ndarray, format: Optional[str] = None) -> None:
    """
    Save an image to file.
    
    Args:
        file_path: Path to save the image
        image_data: Image data as numpy array
        format: Optional format override (e.g., 'PNG', 'TIFF', 'JPEG')
        
    Raises:
        ValueError: If format not supported
        RuntimeError: If saving fails
    """
    try:
        file_path = str(Path(file_path).resolve())
        
        # Determine format
        if format:
            format = format.upper()
            if format not in SUPPORTED_FORMATS.values():
                raise ValueError(f"Unsupported format: {format}")
        else:
            ext = Path(file_path).suffix.lower()
            if ext not in SUPPORTED_FORMATS:
                raise ValueError(f"Unsupported format: {ext}")
            format = SUPPORTED_FORMATS[ext]
            
        logger.info(f"Saving {format} image: {file_path}")
        logger.info(f"Image shape: {image_data.shape}, dtype: {image_data.dtype}")
        
        # Save the image
        iio.imwrite(file_path, image_data, format=format)
        
    except Exception as e:
        logger.error(f"Error saving image to {file_path}: {str(e)}")
        raise
