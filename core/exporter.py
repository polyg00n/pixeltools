"""
exporter.py

Handles exporting RGB tracking results to CSV and NumPy formats.
Useful for later ML workflows or dataset inspection.
"""

import csv
import numpy as np

def export_to_csv(filename, tracking_data):
    """
    Exports pixel RGB sequences and change flags to CSV.
    tracking_data = {
        pixel_id: { 'rgb': [[R,G,B],...], 'flags': [0,1,...] }
    }
    """
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Pixel', 'Frame', 'R', 'G', 'B', 'Changed'])
        for pixel_id, result in tracking_data.items():
            for i, (rgb, flag) in enumerate(zip(result['rgb'], result['flags'])):
                writer.writerow([pixel_id, i, *rgb, flag])

def export_to_npy(filename, tracking_data):
    """
    Exports all tracking data as a .npz file for ML pipelines.
    """
    np.savez(filename, **tracking_data)
