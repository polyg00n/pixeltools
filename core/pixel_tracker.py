"""
pixel_tracker.py

Provides functions for tracking RGB values of specified pixel coordinates
across sequences of image frames.
"""

import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
import json
from typing import Dict, List, Optional, Tuple
from .image_loader import load_image, get_sequence_frames, get_sequence_pattern

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class PixelTracker:
    def __init__(self):
        """Initialize the pixel tracker."""
        self.tracked_pixels = {}  # Dict of (x, y) -> List[Dict]
        self.tolerance = 10
        self.auto_track = True
        
    def set_tolerance(self, value: int):
        """
        Set the tolerance for change detection.
        
        Args:
            value: Tolerance value (0-255)
        """
        self.tolerance = max(0, min(255, value))
        
    def set_auto_track(self, enabled: bool):
        """
        Enable/disable automatic tracking.
        
        Args:
            enabled: Whether to enable auto-tracking
        """
        self.auto_track = enabled
        
    def track_pixel(self, x: int, y: int, frame_data: Optional[np.ndarray] = None):
        """
        Track a pixel's value.
        
        Args:
            x: X coordinate
            y: Y coordinate
            frame_data: Optional frame data to track
        """
        try:
            if frame_data is None:
                return
                
            # Get pixel value
            if 0 <= y < frame_data.shape[0] and 0 <= x < frame_data.shape[1]:
                if len(frame_data.shape) == 2:
                    # Grayscale
                    value = frame_data[y, x]
                    rgb = (value, value, value)
                else:
                    # RGB/RGBA
                    rgb = tuple(frame_data[y, x, :3])
                    
                # Store value
                pixel_key = (x, y)
                if pixel_key not in self.tracked_pixels:
                    self.tracked_pixels[pixel_key] = []
                    
                self.tracked_pixels[pixel_key].append({
                    'frame': len(self.tracked_pixels[pixel_key]),
                    'rgb': rgb
                })
                
                logger.debug(f"Tracked pixel ({x}, {y}): {rgb}")
                
        except Exception as e:
            logger.error(f"Error tracking pixel ({x}, {y}): {str(e)}")
            
    def update_hover(self, x: int, y: int, frame_data: Optional[np.ndarray] = None):
        """
        Update hover information for a pixel.
        
        Args:
            x: X coordinate
            y: Y coordinate
            frame_data: Optional frame data
        """
        try:
            if frame_data is None:
                return
                
            # Get pixel value
            if 0 <= y < frame_data.shape[0] and 0 <= x < frame_data.shape[1]:
                if len(frame_data.shape) == 2:
                    # Grayscale
                    value = frame_data[y, x]
                    rgb = (value, value, value)
                else:
                    # RGB/RGBA
                    rgb = tuple(frame_data[y, x, :3])
                    
                logger.debug(f"Hover pixel ({x}, {y}): {rgb}")
                
        except Exception as e:
            logger.error(f"Error updating hover for pixel ({x}, {y}): {str(e)}")
            
    def clear_tracking(self):
        """Clear all tracked pixels."""
        self.tracked_pixels.clear()
        logger.info("Cleared pixel tracking")
        
    def has_tracking_data(self) -> bool:
        """
        Check if there is any tracking data.
        
        Returns:
            bool: True if there is tracking data
        """
        return len(self.tracked_pixels) > 0
        
    def export_to_csv(self, file_path: str):
        """
        Export tracked pixel data to CSV.
        
        Args:
            file_path: Path to save CSV file
        """
        try:
            if not self.has_tracking_data():
                logger.warning("No tracking data to export")
                return
                
            # Create DataFrame
            data = []
            for (x, y), values in self.tracked_pixels.items():
                for v in values:
                    data.append({
                        'x': x,
                        'y': y,
                        'frame': v['frame'],
                        'r': v['rgb'][0],
                        'g': v['rgb'][1],
                        'b': v['rgb'][2]
                    })
                    
            df = pd.DataFrame(data)
            
            # Save to CSV
            df.to_csv(file_path, index=False)
            logger.info(f"Exported tracking data to {file_path}")
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise
            
    def export_to_npz(self, file_path: str):
        """
        Export tracked pixel data to NPZ.
        
        Args:
            file_path: Path to save NPZ file
        """
        try:
            if not self.has_tracking_data():
                logger.warning("No tracking data to export")
                return
                
            # Convert to numpy arrays
            data = {}
            for (x, y), values in self.tracked_pixels.items():
                key = f"pixel_{x}_{y}"
                frames = np.array([v['frame'] for v in values])
                rgb = np.array([v['rgb'] for v in values])
                data[key] = np.column_stack((frames, rgb))
                
            # Save to NPZ
            np.savez(file_path, **data)
            logger.info(f"Exported tracking data to {file_path}")
            
        except Exception as e:
            logger.error(f"Error exporting to NPZ: {str(e)}")
            raise

    def compute_change_flags(self, tolerance=10):
        """
        Returns binary flags per pixel per frame, indicating whether the
        RGB value changed more than the given tolerance (Euclidean distance).
        """
        flags = {}
        for key, values in self.tracked_pixels.items():
            base = np.array(values[0]['rgb'])
            flags[key] = [(np.linalg.norm(np.array(v['rgb']) - base) > tolerance) for v in values]
        return flags

    def compare_across_sims(self, reference_path, target_frame, tolerance=10):
        """
        Compares pixel values across different simulation folders.
        
        Args:
            reference_path: Path to the reference frame (e.g., sim_0000/cam1.0005.exr)
            target_frame: Frame number to compare (e.g., 5)
            tolerance: RGB difference threshold for flagging changes
            
        Returns:
            dict: Comparison results for each simulation folder
        """
        try:
            reference_path = Path(reference_path)
            if not reference_path.exists():
                logger.error(f"Reference file does not exist: {reference_path}")
                return None
                
            # Get the simulation root directory
            sim_root = reference_path.parent.parent
            if not sim_root.exists():
                logger.error(f"Simulation root directory does not exist: {sim_root}")
                return None
                
            # Get the camera name and frame pattern
            camera_name = reference_path.stem.split('.')[0]
            frame_pattern = f"{camera_name}.{target_frame:04d}.exr"
            
            # Find all simulation folders
            sim_folders = [d for d in sim_root.iterdir() if d.is_dir() and d.name.startswith("sim_")]
            if not sim_folders:
                logger.error(f"No simulation folders found in {sim_root}")
                return None
                
            logger.info(f"Found {len(sim_folders)} simulation folders")
            
            # Load reference frame
            reference_frame = load_image(reference_path)
            if reference_frame is None:
                logger.error(f"Failed to load reference frame: {reference_path}")
                return None
                
            # Initialize results
            results = {
                'reference': {
                    'path': str(reference_path),
                    'pixels': {}
                },
                'comparisons': {}
            }
            
            # Get reference pixel values
            for (x, y), values in self.tracked_pixels.items():
                rgb = values[0]['rgb']
                results['reference']['pixels'][f"x{x}_y{y}"] = rgb
                
            # Compare with other simulations
            for sim_folder in sim_folders:
                sim_name = sim_folder.name
                if sim_name == reference_path.parent.name:
                    continue  # Skip reference simulation
                    
                # Look for matching frame
                frame_path = sim_folder / "renders" / camera_name / frame_pattern
                if not frame_path.exists():
                    logger.warning(f"Frame not found in {sim_name}: {frame_path}")
                    continue
                    
                # Load comparison frame
                comparison_frame = load_image(frame_path)
                if comparison_frame is None:
                    logger.warning(f"Failed to load comparison frame: {frame_path}")
                    continue
                    
                # Compare pixels
                sim_results = {
                    'path': str(frame_path),
                    'pixels': {},
                    'differences': {}
                }
                
                for (x, y), values in self.tracked_pixels.items():
                    ref_rgb = np.array(results['reference']['pixels'][f"x{x}_y{y}"])
                    comp_rgb = comparison_frame[y, x]
                    diff = np.linalg.norm(comp_rgb - ref_rgb)
                    changed = diff > tolerance
                    
                    sim_results['pixels'][f"x{x}_y{y}"] = comp_rgb.tolist()
                    sim_results['differences'][f"x{x}_y{y}"] = {
                        'delta': float(diff),
                        'changed': bool(changed)
                    }
                    
                results['comparisons'][sim_name] = sim_results
                
            return results
            
        except Exception as e:
            logger.error(f"Error comparing across simulations: {str(e)}")
            return None

    def export_to_csv(self, output_path):
        """
        Exports tracked pixel data to a CSV file.
        Format: frame_number, pixel_coords, r, g, b, changed_flag
        """
        rows = []
        flags = self.compute_change_flags()
        
        for frame_idx, frame_num in enumerate(self.frame_numbers):
            for key, values in self.data.items():
                x, y = key.split('_')
                x = int(x[1:])  # Remove 'x' prefix
                y = int(y[1:])  # Remove 'y' prefix
                rgb = values[frame_idx]
                changed = flags[key][frame_idx]
                rows.append({
                    'frame': frame_num,
                    'x': x,
                    'y': y,
                    'r': rgb[0],
                    'g': rgb[1],
                    'b': rgb[2],
                    'changed': changed
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        return output_path

    def export_to_npz(self, output_path):
        """
        Exports tracked pixel data to an NPZ file.
        Includes RGB values, coordinates, frame numbers, and change flags.
        """
        data_dict = {
            'frame_numbers': np.array(self.frame_numbers),
            'coordinates': np.array(self.coordinates),
        }
        
        # Add RGB data for each pixel
        for key, values in self.data.items():
            data_dict[f'rgb_{key}'] = np.array(values)
        
        # Add change flags
        flags = self.compute_change_flags()
        for key, values in flags.items():
            data_dict[f'changed_{key}'] = np.array(values)
        
        np.savez(output_path, **data_dict)
        return output_path

    def export_metadata(self, output_path):
        """
        Exports tracking metadata to a JSON file.
        Includes coordinates, frame count, and other tracking parameters.
        """
        metadata = {
            'coordinates': self.coordinates,
            'frame_count': len(self.frame_numbers),
            'pixel_count': len(self.coordinates),
            'frame_numbers': self.frame_numbers
        }
        
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        return output_path

    def export_comparison_to_csv(self, comparison_results, output_path):
        """
        Exports cross-simulation comparison results to a CSV file.
        
        Args:
            comparison_results: Results from compare_across_sims()
            output_path: Path to save the CSV file
            
        Returns:
            str: Path to the saved CSV file
        """
        try:
            rows = []
            
            # Add reference data
            for pixel_key, rgb in comparison_results['reference']['pixels'].items():
                x, y = pixel_key.split('_')
                x = int(x[1:])  # Remove 'x' prefix
                y = int(y[1:])  # Remove 'y' prefix
                rows.append({
                    'simulation': 'reference',
                    'path': comparison_results['reference']['path'],
                    'x': x,
                    'y': y,
                    'r': rgb[0],
                    'g': rgb[1],
                    'b': rgb[2],
                    'delta': 0.0,
                    'changed': False
                })
            
            # Add comparison data
            for sim_name, sim_data in comparison_results['comparisons'].items():
                for pixel_key, rgb in sim_data['pixels'].items():
                    x, y = pixel_key.split('_')
                    x = int(x[1:])  # Remove 'x' prefix
                    y = int(y[1:])  # Remove 'y' prefix
                    diff_data = sim_data['differences'][pixel_key]
                    rows.append({
                        'simulation': sim_name,
                        'path': sim_data['path'],
                        'x': x,
                        'y': y,
                        'r': rgb[0],
                        'g': rgb[1],
                        'b': rgb[2],
                        'delta': diff_data['delta'],
                        'changed': diff_data['changed']
                    })
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(rows)
            df.to_csv(output_path, index=False)
            logger.info(f"Exported comparison results to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting comparison results: {str(e)}")
            return None
