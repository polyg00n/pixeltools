"""
core/encoder.py

Handles encoding of image sequences to MP4 video format.
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

def encode_single_sequence(
    sequence_dir: str,
    output_path: Optional[str] = None,
    fps: int = 30,
    quality: int = 95,
    max_size: Optional[Tuple[int, int]] = None
) -> bool:
    """
    Encode a sequence of images to MP4 video.
    
    Args:
        sequence_dir: Directory containing the image sequence
        output_path: Optional output path for the video
        fps: Frames per second
        quality: Video quality (0-100)
        max_size: Optional maximum dimensions (width, height)
        
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
        logger.info(f"Found {len(image_files)} frames")
        
        # Load first frame to get dimensions
        first_frame = iio.imread(str(image_files[0]))
        height, width = first_frame.shape[:2]
        
        # Calculate output dimensions if max_size is specified
        if max_size:
            max_width, max_height = max_size
            if width > max_width or height > max_height:
                scale = min(max_width / width, max_height / height)
                width = int(width * scale)
                height = int(height * scale)
                logger.info(f"Resizing to {width}x{height}")
        
        # Set output path
        if output_path is None:
            output_path = sequence_dir / "preview.mp4"
        else:
            output_path = Path(output_path)
            
        # Create video writer
        writer = iio.get_writer(
            str(output_path),
            fps=fps,
            quality=quality,
            macro_block_size=16  # Ensures dimensions are divisible by 16
        )
        
        # Process frames
        for frame_path in image_files:
            try:
                # Load frame
                frame = iio.imread(str(frame_path))
                
                # Convert to 8-bit if needed
                if frame.dtype != np.uint8:
                    if frame.max() > 1.0:
                        frame = frame / frame.max()
                    frame = (frame * 255).astype(np.uint8)
                
                # Resize if needed
                if max_size and (frame.shape[1] != width or frame.shape[0] != height):
                    frame = iio.imresize(frame, (height, width))
                
                # Write frame
                writer.append_data(frame)
                logger.debug(f"Processed frame: {frame_path.name}")
                
            except Exception as e:
                logger.error(f"Error processing frame {frame_path}: {str(e)}")
                continue
        
        # Close writer
        writer.close()
        logger.info(f"Video saved to: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error encoding sequence: {str(e)}")
        return False

def encode_multiple_sequences(
    sequences_dir: str,
    output_dir: Optional[str] = None,
    fps: int = 30,
    quality: int = 95,
    max_size: Optional[Tuple[int, int]] = None
) -> bool:
    """
    Encode multiple image sequences to MP4 videos.
    
    Args:
        sequences_dir: Directory containing multiple sequence directories
        output_dir: Optional output directory for videos
        fps: Frames per second
        quality: Video quality (0-100)
        max_size: Optional maximum dimensions (width, height)
        
    Returns:
        bool: True if all sequences were encoded successfully
    """
    try:
        sequences_dir = Path(sequences_dir)
        if not sequences_dir.exists():
            logger.error(f"Sequences directory not found: {sequences_dir}")
            return False
            
        # Get all sequence directories
        sequence_dirs = [d for d in sequences_dir.iterdir() if d.is_dir()]
        if not sequence_dirs:
            logger.error(f"No sequence directories found in {sequences_dir}")
            return False
            
        logger.info(f"Found {len(sequence_dirs)} sequences")
        
        # Process each sequence
        success = True
        for seq_dir in sequence_dirs:
            if output_dir:
                output_path = Path(output_dir) / f"{seq_dir.name}.mp4"
            else:
                output_path = None
                
            if not encode_single_sequence(
                str(seq_dir),
                str(output_path) if output_path else None,
                fps,
                quality,
                max_size
            ):
                success = False
                logger.error(f"Failed to encode sequence in {seq_dir}")
                
        return success
        
    except Exception as e:
        logger.error(f"Error encoding sequences: {str(e)}")
        return False
