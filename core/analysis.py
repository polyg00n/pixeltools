"""
core/analysis.py

Provides functions for analyzing image sequence datasets.
"""

import logging
from pathlib import Path
import numpy as np
from collections import defaultdict
from .image_loader import get_sequence_frames, get_sequence_pattern

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def analyze_dataset(root_folder):
    """
    Analyzes a dataset of image sequences, collecting statistics and metadata.
    Recursively searches through subfolders for image sequences.
    
    Parameters:
        root_folder (Path): Root directory containing simulation folders
        
    Returns:
        dict: Dataset statistics and metadata
    """
    try:
        root_folder = Path(root_folder)
        if not root_folder.exists():
            logger.error(f"Root folder does not exist: {root_folder}")
            return None

        logger.info(f"Starting dataset analysis of {root_folder}")
        
        # Initialize statistics
        stats = {
            'total_folders': 0,
            'total_sequences': 0,
            'total_frames': 0,
            'sequence_types': defaultdict(int),
            'frame_counts': defaultdict(int),
            'folder_sizes': defaultdict(int),
            'errors': [],
            'sequence_locations': []  # Track where sequences are found
        }

        # Recursively find all subfolders
        try:
            all_folders = [f for f in root_folder.rglob('*') if f.is_dir()]
            logger.info(f"Found {len(all_folders)} total subfolders")
        except Exception as e:
            logger.error(f"Error listing subfolders: {str(e)}")
            stats['errors'].append(f"Failed to list subfolders: {str(e)}")
            return stats

        stats['total_folders'] = len(all_folders)

        # Analyze each folder
        for folder in all_folders:
            try:
                logger.info(f"Analyzing folder: {folder}")
                
                # Get folder size
                try:
                    folder_size = sum(f.stat().st_size for f in folder.glob('*') if f.is_file())
                    stats['folder_sizes'][str(folder.relative_to(root_folder))] = folder_size
                    logger.debug(f"Folder size: {folder_size/1024/1024:.2f} MB")
                except Exception as e:
                    logger.error(f"Error calculating folder size: {str(e)}")
                    stats['errors'].append(f"Failed to get size of {folder}: {str(e)}")

                # Find all image files in this folder (not recursive)
                try:
                    image_files = list(folder.glob("*.exr")) + list(folder.glob("*.png"))
                    logger.info(f"Found {len(image_files)} image files in {folder}")
                except Exception as e:
                    logger.error(f"Error finding image files: {str(e)}")
                    stats['errors'].append(f"Failed to list images in {folder}: {str(e)}")
                    continue

                if not image_files:
                    logger.debug(f"No image files found in {folder}")
                    continue

                # Detect sequence pattern
                try:
                    pattern, padding, ext = get_sequence_pattern(image_files[0])
                    if pattern:
                        logger.info(f"Detected sequence pattern: {pattern}")
                        stats['sequence_types'][ext] += 1
                        
                        # Get all frames in sequence
                        frames = get_sequence_frames(folder, pattern)
                        if frames:
                            frame_count = len(frames)
                            relative_path = str(folder.relative_to(root_folder))
                            stats['frame_counts'][relative_path] = frame_count
                            stats['total_frames'] += frame_count
                            stats['total_sequences'] += 1
                            stats['sequence_locations'].append(relative_path)
                            logger.info(f"Found {frame_count} frames in sequence at {relative_path}")
                        else:
                            logger.warning(f"No frames found matching pattern {pattern} in {folder}")
                    else:
                        logger.debug(f"No sequence pattern detected in {folder}")
                except Exception as e:
                    logger.error(f"Error analyzing sequence pattern: {str(e)}")
                    stats['errors'].append(f"Failed to analyze sequence in {folder}: {str(e)}")

            except Exception as e:
                logger.error(f"Error analyzing folder {folder}: {str(e)}")
                stats['errors'].append(f"Failed to analyze {folder}: {str(e)}")
                continue

        logger.info("Dataset analysis complete")
        return stats

    except Exception as e:
        logger.error(f"Critical error in dataset analysis: {str(e)}")
        return None

def print_dataset_stats(stats):
    """
    Prints dataset statistics in a readable format.
    
    Parameters:
        stats (dict): Dataset statistics from analyze_dataset()
    """
    try:
        if not stats:
            logger.error("No statistics to print")
            return

        logger.info("\nDataset Analysis Results:")
        logger.info("=" * 50)
        
        # Print basic statistics
        logger.info(f"Total Folders: {stats['total_folders']}")
        logger.info(f"Total Sequences: {stats['total_sequences']}")
        logger.info(f"Total Frames: {stats['total_frames']}")
        
        # Print sequence types
        logger.info("\nSequence Types:")
        for ext, count in stats['sequence_types'].items():
            logger.info(f"  {ext}: {count} sequences")
        
        # Print frame counts
        logger.info("\nFrame Counts per Folder:")
        for folder, count in stats['frame_counts'].items():
            logger.info(f"  {folder}: {count} frames")
        
        # Print folder sizes
        logger.info("\nFolder Sizes:")
        for folder, size in stats['folder_sizes'].items():
            logger.info(f"  {folder}: {size/1024/1024:.2f} MB")
        
        # Print sequence locations
        logger.info("\nSequence Locations:")
        for location in stats['sequence_locations']:
            logger.info(f"  {location}")
        
        # Print any errors
        if stats['errors']:
            logger.warning("\nErrors Encountered:")
            for error in stats['errors']:
                logger.warning(f"  {error}")

    except Exception as e:
        logger.error(f"Error printing dataset statistics: {str(e)}")
