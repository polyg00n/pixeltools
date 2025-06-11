"""
core/extractor.py

Handles extraction of AOVs from EXR sequences and conversion to other formats.
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

def extract_features_from_sequence(
    sequence_dir: str,
    output_dir: str,
    feature_names: List[str],
    max_size: Optional[Tuple[int, int]] = None
) -> bool:
    """
    Extract features from an image sequence.
    
    Args:
        sequence_dir: Directory containing the image sequence
        output_dir: Directory to save extracted features
        feature_names: List of feature names to extract
        max_size: Optional maximum dimensions for output images
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        sequence_dir = Path(sequence_dir)
        output_dir = Path(output_dir)
        
        if not sequence_dir.exists():
            logger.error(f"Sequence directory not found: {sequence_dir}")
            return False
            
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        # Process each frame
        for frame_path in image_files:
            try:
                # Load frame
                frame = iio.imread(str(frame_path))
                
                # Extract features
                for feature_name in feature_names:
                    try:
                        # Get feature data
                        feature_data = extract_feature(frame, feature_name)
                        if feature_data is None:
                            continue
                            
                        # Create output path
                        feature_dir = output_dir / feature_name
                        feature_dir.mkdir(exist_ok=True)
                        output_path = feature_dir / frame_path.name
                        
                        # Save feature
                        save_feature(feature_data, str(output_path), max_size)
                        logger.debug(f"Saved {feature_name} for frame {frame_path.name}")
                        
                    except Exception as e:
                        logger.error(f"Error extracting {feature_name} from {frame_path}: {str(e)}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error processing frame {frame_path}: {str(e)}")
                continue
                
        logger.info(f"Feature extraction complete. Output directory: {output_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}")
        return False

def extract_feature(image: np.ndarray, feature_name: str) -> Optional[np.ndarray]:
    """
    Extract a specific feature from an image.
    
    Args:
        image: Input image
        feature_name: Name of feature to extract
        
    Returns:
        Optional[np.ndarray]: Extracted feature data or None if extraction fails
    """
    try:
        # Convert to float32 for processing
        if image.dtype != np.float32:
            if image.max() > 1.0:
                image = image / image.max()
            image = image.astype(np.float32)
            
        # Extract feature based on name
        if feature_name == 'edges':
            # Simple edge detection using gradient
            dx = np.gradient(image, axis=1)
            dy = np.gradient(image, axis=0)
            return np.sqrt(dx**2 + dy**2)
            
        elif feature_name == 'intensity':
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                return np.mean(image, axis=2)
            return image
            
        elif feature_name == 'gradient':
            # Calculate gradient magnitude
            dx = np.gradient(image, axis=1)
            dy = np.gradient(image, axis=0)
            return np.sqrt(dx**2 + dy**2)
            
        else:
            logger.error(f"Unknown feature: {feature_name}")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting feature {feature_name}: {str(e)}")
        return None

def save_feature(
    feature_data: np.ndarray,
    output_path: str,
    max_size: Optional[Tuple[int, int]] = None
) -> bool:
    """
    Save feature data to file.
    
    Args:
        feature_data: Feature data to save
        output_path: Path to save the feature
        max_size: Optional maximum dimensions
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Resize if needed
        if max_size:
            height, width = feature_data.shape[:2]
            if width > max_size[0] or height > max_size[1]:
                scale = min(max_size[0] / width, max_size[1] / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                feature_data = iio.imresize(feature_data, (new_height, new_width))
                
        # Convert to 8-bit if needed
        if feature_data.dtype != np.uint8:
            if feature_data.max() > 1.0:
                feature_data = feature_data / feature_data.max()
            feature_data = (feature_data * 255).astype(np.uint8)
            
        # Save feature
        iio.imwrite(output_path, feature_data)
        return True
        
    except Exception as e:
        logger.error(f"Error saving feature to {output_path}: {str(e)}")
        return False
