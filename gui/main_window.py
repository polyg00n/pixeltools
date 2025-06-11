"""
main_window.py

Main GUI window for PixelTools — includes dockable log console, buttons for launching 
various tools (dataset analysis, sequence encoding, cleanup, etc.), and connects GUI events 
to core processing functions. Designed with verbose comments to serve as a learning tool.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QLabel, QPushButton, QVBoxLayout,
    QWidget, QTextEdit, QDockWidget, QLineEdit, QHBoxLayout, QInputDialog,
    QGroupBox, QSpinBox, QCheckBox, QComboBox, QDialog, QScrollArea, QMessageBox,
    QProgressBar, QTabWidget
)
from PyQt5.QtCore import Qt, QDateTime, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

# Core functionality modules
from core.analysis import analyze_dataset, print_dataset_stats
from core.encoder import encode_single_sequence, encode_multiple_sequences
from core.thumbnail import create_thumbnail_video
from core.visualizer import create_thumbnail_grid, create_sequence_preview
from core.cleanup import cleanup_temp_files
from core.pixel_tracker import PixelTracker
from gui.image_viewer import ImageViewer

from pathlib import Path
import sys
import io
import logging
import json
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PixelTools")
        self.setMinimumSize(1200, 800)
        
        # Initialize components
        self.image_viewer = ImageViewer()
        self.pixel_tracker = PixelTracker()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Add file loading controls
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout(file_group)
        
        # Load sequence button
        self.load_btn = QPushButton("Load Sequence")
        self.load_btn.clicked.connect(self.load_sequence)
        file_layout.addWidget(self.load_btn)
        
        # Load single image button
        self.load_single_btn = QPushButton("Load Single Image")
        self.load_single_btn.clicked.connect(self.load_single_image)
        file_layout.addWidget(self.load_single_btn)
        
        left_layout.addWidget(file_group)
        
        # Add pixel tracking controls
        tracking_group = QGroupBox("Pixel Tracking")
        tracking_layout = QVBoxLayout(tracking_group)
        
        # Tolerance control
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("Tolerance:"))
        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(0, 255)
        self.tolerance_spin.setValue(10)
        self.tolerance_spin.valueChanged.connect(self.pixel_tracker.set_tolerance)
        tolerance_layout.addWidget(self.tolerance_spin)
        tracking_layout.addLayout(tolerance_layout)
        
        # Auto-track checkbox
        self.auto_track_cb = QCheckBox("Auto-track on click")
        self.auto_track_cb.setChecked(True)
        self.auto_track_cb.stateChanged.connect(self.pixel_tracker.set_auto_track)
        tracking_layout.addWidget(self.auto_track_cb)
        
        # Clear tracking button
        self.clear_btn = QPushButton("Clear Tracking")
        self.clear_btn.clicked.connect(self.pixel_tracker.clear_tracking)
        tracking_layout.addWidget(self.clear_btn)
        
        left_layout.addWidget(tracking_group)
        
        # Add export controls
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        
        # Export to CSV button
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        export_layout.addWidget(self.export_csv_btn)
        
        # Export to NPZ button
        self.export_npz_btn = QPushButton("Export to NPZ")
        self.export_npz_btn.clicked.connect(self.export_to_npz)
        export_layout.addWidget(self.export_npz_btn)
        
        left_layout.addWidget(export_group)
        
        # Add tools
        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout(tools_group)
        
        # Analyze dataset button
        self.analyze_btn = QPushButton("Analyze Dataset")
        self.analyze_btn.clicked.connect(self.analyze_dataset)
        tools_layout.addWidget(self.analyze_btn)
        
        # Encode sequence button
        self.encode_btn = QPushButton("Encode Sequence to MP4")
        self.encode_btn.clicked.connect(self.encode_sequence)
        tools_layout.addWidget(self.encode_btn)
        
        # Create thumbnail button
        self.thumbnail_btn = QPushButton("Create Thumbnail Summary")
        self.thumbnail_btn.clicked.connect(self.create_thumbnail)
        tools_layout.addWidget(self.thumbnail_btn)
        
        # Extract features button
        self.extract_btn = QPushButton("Extract Features")
        self.extract_btn.clicked.connect(self.extract_features)
        tools_layout.addWidget(self.extract_btn)
        
        left_layout.addWidget(tools_group)
        
        # Add stretch to push everything to the top
        left_layout.addStretch()
        
        # Add left panel to main layout
        layout.addWidget(left_panel, stretch=1)
        
        # Add image viewer to main layout
        layout.addWidget(self.image_viewer, stretch=4)
        
        # Connect signals
        self.image_viewer.pixel_clicked.connect(self.pixel_tracker.track_pixel)
        self.image_viewer.pixel_hovered.connect(self.pixel_tracker.update_hover)
        
        # Initialize state
        self.current_sequence = None
        self.current_frame = None
        
    def load_sequence(self):
        """Load an image sequence."""
        try:
            # Get sequence directory
            sequence_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Sequence Directory",
                str(Path.home())
            )
            if not sequence_dir:
                return
                
            # Get sequence frames
            frames = get_sequence_frames(sequence_dir)
            if not frames:
                QMessageBox.warning(
                    self,
                    "No Frames Found",
                    f"No supported image files found in {sequence_dir}"
                )
                return
                
            # Store sequence info
            self.current_sequence = {
                'dir': sequence_dir,
                'frames': frames,
                'current_index': 0
            }
            
            # Load first frame
            self.load_frame(0)
            
        except Exception as e:
            logger.error(f"Error loading sequence: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load sequence: {str(e)}"
            )
            
    def load_single_image(self):
        """Load a single image."""
        try:
            # Get image file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Image",
                str(Path.home()),
                "Images (*.tiff *.tif *.png *.jpg *.jpeg)"
            )
            if not file_path:
                return
                
            # Load image
            image_data, metadata = load_image(file_path)
            
            # Display image
            self.image_viewer.set_image(image_data)
            
            # Clear sequence state
            self.current_sequence = None
            self.current_frame = file_path
            
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load image: {str(e)}"
            )
            
    def load_frame(self, index: int):
        """Load a specific frame from the current sequence."""
        try:
            if not self.current_sequence:
                return
                
            frames = self.current_sequence['frames']
            if not 0 <= index < len(frames):
                return
                
            # Load frame
            image_data, metadata = load_image(frames[index])
            
            # Display frame
            self.image_viewer.set_image(image_data)
            
            # Update state
            self.current_sequence['current_index'] = index
            self.current_frame = frames[index]
            
        except Exception as e:
            logger.error(f"Error loading frame: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load frame: {str(e)}"
            )
            
    def export_to_csv(self):
        """Export tracked pixel data to CSV."""
        try:
            if not self.pixel_tracker.has_tracking_data():
                QMessageBox.warning(
                    self,
                    "No Data",
                    "No pixel tracking data to export"
                )
                return
                
            # Get save path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save CSV",
                str(Path.home()),
                "CSV Files (*.csv)"
            )
            if not file_path:
                return
                
            # Export data
            self.pixel_tracker.export_to_csv(file_path)
            
            QMessageBox.information(
                self,
                "Success",
                f"Data exported to {file_path}"
            )
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to export data: {str(e)}"
            )
            
    def export_to_npz(self):
        """Export tracked pixel data to NPZ."""
        try:
            if not self.pixel_tracker.has_tracking_data():
                QMessageBox.warning(
                    self,
                    "No Data",
                    "No pixel tracking data to export"
                )
                return
                
            # Get save path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save NPZ",
                str(Path.home()),
                "NPZ Files (*.npz)"
            )
            if not file_path:
                return
                
            # Export data
            self.pixel_tracker.export_to_npz(file_path)
            
            QMessageBox.information(
                self,
                "Success",
                f"Data exported to {file_path}"
            )
            
        except Exception as e:
            logger.error(f"Error exporting to NPZ: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to export data: {str(e)}"
            )
            
    def analyze_dataset(self):
        """Analyze a dataset directory."""
        try:
            # Get dataset directory
            dataset_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Dataset Directory",
                str(Path.home())
            )
            if not dataset_dir:
                return
                
            # Analyze dataset
            stats = analyze_dataset(dataset_dir)
            
            # Show results
            QMessageBox.information(
                self,
                "Dataset Analysis",
                print_dataset_stats(stats)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing dataset: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to analyze dataset: {str(e)}"
            )
            
    def encode_sequence(self):
        """Encode a sequence to MP4."""
        try:
            # Get sequence directory
            sequence_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Sequence Directory",
                str(Path.home())
            )
            if not sequence_dir:
                return
                
            # Get output path
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Video",
                str(Path.home()),
                "MP4 Files (*.mp4)"
            )
            if not output_path:
                return
                
            # Get encoding options
            fps, ok = QInputDialog.getInt(
                self,
                "Frames Per Second",
                "Enter FPS:",
                30, 1, 120, 1
            )
            if not ok:
                return
                
            quality, ok = QInputDialog.getInt(
                self,
                "Video Quality",
                "Enter quality (0-100):",
                95, 0, 100, 5
            )
            if not ok:
                return
                
            # Encode sequence
            if encode_single_sequence(
                sequence_dir,
                output_path,
                fps=fps,
                quality=quality
            ):
                QMessageBox.information(
                    self,
                    "Success",
                    f"Video saved to {output_path}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to encode sequence"
                )
                
        except Exception as e:
            logger.error(f"Error encoding sequence: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to encode sequence: {str(e)}"
            )
            
    def create_thumbnail(self):
        """Create a thumbnail summary video."""
        try:
            # Get sequences directory
            sequences_dir = QFileDialog.getExistingDirectory(
                self,
                "Select Sequences Directory",
                str(Path.home())
            )
            if not sequences_dir:
                return
                
            # Get output path
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Thumbnail",
                str(Path.home()),
                "Images (*.png)"
            )
            if not output_path:
                return
                
            # Create thumbnail
            if create_sequence_preview(sequences_dir, output_path):
                QMessageBox.information(
                    self,
                    "Success",
                    f"Thumbnail saved to {output_path}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to create thumbnail"
                )
                
        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to create thumbnail: {str(e)}"
            )
            
    def extract_features(self):
        """Extract features from the current image."""
        try:
            if not self.current_frame:
                QMessageBox.warning(
                    self,
                    "No Image",
                    "Please load an image first"
                )
                return
                
            # Get output path
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Features",
                str(Path.home()),
                "NPZ Files (*.npz)"
            )
            if not output_path:
                return
                
            # Load image data
            image_data, metadata = load_image(self.current_frame)
            if image_data is None:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to load image data"
                )
                return
                
            # Extract basic features
            features = {
                'mean': np.mean(image_data),
                'std': np.std(image_data),
                'min': np.min(image_data),
                'max': np.max(image_data),
                'shape': image_data.shape,
                'dtype': str(image_data.dtype)
            }
            
            # Add metadata if available
            if metadata:
                features['metadata'] = metadata
                
            # Save features
            np.savez(output_path, **features)
            QMessageBox.information(
                self,
                "Success",
                f"Features saved to {output_path}"
            )
                
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to extract features: {str(e)}"
            )
            
    def on_pixel_selected(self, x, y):
        """Handle pixel selection from the image viewer."""
        if self.auto_track_cb.isChecked():
            self.pixel_tracker.track_pixel(x, y, self.image_viewer.current_image)
            self.log(f"Tracking pixel at ({x}, {y})")
            
    def clear_tracking(self):
        """Clear all tracked pixels."""
        self.pixel_tracker.clear_tracking()
        self.image_viewer.clear_tracked_pixels()
        self.log("Cleared all tracked pixels")
        
    def export_metadata(self):
        """Export tracking metadata to JSON."""
        try:
            if not self.pixel_tracker.has_tracking_data():
                QMessageBox.warning(
                    self,
                    "No Data",
                    "No pixel tracking data to export"
                )
                return
                
            # Get save path
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Metadata",
                str(Path.home()),
                "JSON Files (*.json)"
            )
            if not file_path:
                return
                
            # Export metadata
            metadata = {
                'tolerance': self.tolerance_spin.value(),
                'auto_track': self.auto_track_cb.isChecked(),
                'pixels': self.pixel_tracker.tracked_pixels
            }
            
            with open(file_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            QMessageBox.information(
                self,
                "Success",
                f"Metadata saved to {file_path}"
            )
            
        except Exception as e:
            logger.error(f"Error exporting metadata: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to export metadata: {str(e)}"
            )

    def log(self, message):
        """
        Utility function to write timestamped messages to the log console.
        Called by all tool functions.
        """
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.log_console.append(f"[{timestamp}] {message}")
        self.log_console.ensureCursorVisible()

    def run_analysis(self):
        """
        Launches dataset analysis tool.
        Prompts user to select folder, passes it to analyze_dataset(),
        and prints the results into the log.
        """
        try:
            folder = QFileDialog.getExistingDirectory(self, "Select Dataset Folder")
            if not folder:
                self.log("Dataset analysis cancelled.")
                return

            self.log(f"Starting dataset analysis on: {folder}")
            self.log("This may take a while for large datasets...")

            try:
                dataset = analyze_dataset(Path(folder))
                if dataset is None:
                    self.log("Analysis failed - check log for details")
                    return

                # Create a string buffer to capture the output
                buffer = io.StringIO()
                sys_stdout = sys.stdout
                sys.stdout = buffer

                try:
                    print_dataset_stats(dataset)
                finally:
                    # Restore stdout
                    sys.stdout = sys_stdout
                    output = buffer.getvalue()
                    buffer.close()

                # Log the results
                self.log(output)

                # Log any errors that occurred
                if dataset.get('errors'):
                    self.log("\nErrors encountered during analysis:")
                    for error in dataset['errors']:
                        self.log(f"  - {error}")

            except Exception as e:
                self.log(f"Error during analysis: {str(e)}")
                import traceback
                self.log("Detailed error information:")
                self.log(traceback.format_exc())

        except Exception as e:
            self.log(f"Critical error in analysis tool: {str(e)}")
            import traceback
            self.log("Detailed error information:")
            self.log(traceback.format_exc())

    def extract_aovs(self):
        """
        Extracts specified AOVs from EXR files in a folder.
        AOVs are read from input field.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder for AOV Extraction")
        if not folder:
            self.log("AOV extraction cancelled.")
            return

        aov_names = [a.strip() for a in self.aov_input.text().split(',') if a.strip()]
        if not aov_names:
            self.log("No AOVs entered.")
            return

        self.log(f"Extracting AOVs: {aov_names} from {folder}")
        try:
            extract_aovs_from_sequences(
                base_dir=Path(folder),
                aov_names=aov_names,
                output_format="png",
                colormap="viridis",
                normalize=True,
                encode_video=True,
                parallel=True
            )
            self.log("AOV extraction complete.")
        except Exception as e:
            self.log(f"Error during AOV extraction: {e}")

    def encode_video(self):
        """
        Encodes all .png frames in a folder to an MP4 video.
        Prompts for folder using QFileDialog.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Encode")
        if not folder:
            self.log("Encoding cancelled.")
            return

        # Get encoding options
        options = {}
        
        # Recursive option
        recursive, ok = QInputDialog.getItem(
            self, "Recursive Search", "Search subfolders for sequences?",
            ["Yes", "No"], 0, False
        )
        if not ok:
            self.log("Encoding cancelled: no recursive option selected.")
            return
        options['recursive'] = recursive == "Yes"
        
        # Codec selection
        codecs = {
            "H.264 (mp4v)": "mp4v",
            "H.264 (avc1)": "avc1",
            "H.264 (h264)": "h264"
        }
        codec, ok = QInputDialog.getItem(
            self, "Select Codec", "Choose video codec:",
            list(codecs.keys()), 0, False
        )
        if not ok:
            self.log("Encoding cancelled: no codec selected.")
            return
        options['codec'] = codecs[codec]

        # FPS selection
        fps, ok = QInputDialog.getInt(
            self, "Frames Per Second", "Enter FPS:",
            24, 1, 120, 1
        )
        if not ok:
            self.log("Encoding cancelled: no FPS selected.")
            return
        options['fps'] = fps

        # Quality selection
        quality, ok = QInputDialog.getInt(
            self, "Video Quality", "Enter quality (0-100):",
            95, 0, 100, 5
        )
        if not ok:
            self.log("Encoding cancelled: no quality selected.")
            return
        options['quality'] = quality

        # Max size selection
        max_size, ok = QInputDialog.getText(
            self, "Maximum Size", "Enter max size (width,height) or leave empty:"
        )
        if ok and max_size.strip():
            try:
                w, h = map(int, max_size.split(','))
                options['max_size'] = (w, h)
            except ValueError:
                self.log("Invalid size format. Using original size.")

        try:
            self.log(f"Starting video encoding{' (recursive)' if options['recursive'] else ''}")
            success = encode_sequence(
                Path(folder),
                output_path=Path(folder) / "preview.mp4",
                fps=options['fps'],
                codec=options['codec'],
                quality=options['quality'],
                max_size=options.get('max_size'),
                recursive=options['recursive']
            )
            if success:
                self.log("Sequence encoding complete.")
            else:
                self.log("Failed to encode sequence(s).")
        except Exception as e:
            self.log(f"Encoding error: {str(e)}")
            import traceback
            self.log("Detailed error information:")
            self.log(traceback.format_exc())

    def make_thumbnail_video(self):
        """
        Creates a thumbnail-style comparison frame showing the same frame
        number from multiple simulations.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder for Thumbnail Video")
        if not folder:
            self.log("Thumbnail generation cancelled.")
            return
        try:
            create_thumbnail_video(Path(folder))
            self.log("Thumbnail video created.")
        except Exception as e:
            self.log(f"Thumbnail video error: {e}")

    def compare_aovs(self):
        """
        Creates a grid image showing different AOVs from a single EXR frame.
        Asks the user which AOVs to include.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Select EXR File")
        if not file_path:
            self.log("Comparison cancelled.")
            return

        aov_input, ok = QInputDialog.getText(self, "Select AOVs", "Enter AOVs to compare (comma-separated):")
        if not ok or not aov_input.strip():
            self.log("Comparison cancelled: no AOVs entered.")
            return

        aov_list = [a.strip() for a in aov_input.split(',') if a.strip()]

        try:
            create_aov_comparison(Path(file_path), aovs=aov_list)
            self.log(f"AOV comparison image created for: {', '.join(aov_list)}")
        except Exception as e:
            self.log(f"Comparison error: {e}")

    def cleanup_files(self):
        """
        Scans and removes temp files: preview.mp4, _aov_* folders, cache dirs, etc.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Clean")
        if not folder:
            self.log("Cleanup cancelled.")
            return
        try:
            cleanup_temp_files(Path(folder))
            self.log("Cleanup complete.")
        except Exception as e:
            self.log(f"Cleanup error: {e}")

    def on_aov_changed(self, aov_name):
        """Handle AOV selection change."""
        if hasattr(self, 'current_image_path') and self.current_image_path:
            # Reload the current image with the selected AOV
            try:
                from core.image_loader import load_image
                image = load_image(self.current_image_path, aov=aov_name if aov_name != "RGB" else None)
                if image is not None:
                    self.image_viewer.display_image(image)
                    self.log(f"Switched to AOV: {aov_name}")
                else:
                    self.log(f"Failed to load AOV: {aov_name}")
            except Exception as e:
                self.log(f"Error switching AOV: {str(e)}")
                import traceback
                self.log(traceback.format_exc())

    def load_image(self):
        """Load an image file and display it in the viewer."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Image", "", "Image Files (*.exr *.png *.jpg *.jpeg)"
        )
        if not file_path:
            return
            
        try:
            from core.image_loader import load_image, get_exr_aovs
            
            # First try to load the image in RGB mode
            image = load_image(file_path)
            if image is None:
                self.log(f"Failed to load image: {file_path}")
                return
                
            # If successful, store the path and display the image
            self.current_image_path = file_path
            self.image_viewer.display_image(image)
            self.log(f"Loaded image: {file_path}")
            
            # Now populate AOV selector if it's an EXR file
            if file_path.lower().endswith('.exr'):
                try:
                    aovs = get_exr_aovs(file_path)
                    self.aov_combo.clear()
                    self.aov_combo.addItem("RGB")
                    if aovs:
                        self.aov_combo.addItems(aovs)
                        self.log(f"Available AOVs: {', '.join(aovs)}")
                    else:
                        self.log("No additional AOVs found in EXR file")
                except Exception as e:
                    self.log(f"Warning: Could not read AOVs: {str(e)}")
                    self.aov_combo.clear()
                    self.aov_combo.addItem("RGB")
            else:
                # For non-EXR files, just show RGB option
                self.aov_combo.clear()
                self.aov_combo.addItem("RGB")
                
        except Exception as e:
            self.log(f"Error loading image: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            # Reset AOV selector to RGB only
            self.aov_combo.clear()
            self.aov_combo.addItem("RGB")

    def compare_across_sequence(self):
        """Compare tracked pixels across all frames in a sequence."""
        if not self.pixel_tracker.coordinates:
            self.log("No pixels being tracked. Please select pixels first.")
            return
            
        folder = QFileDialog.getExistingDirectory(self, "Select Sequence Folder")
        if not folder:
            self.log("Sequence comparison cancelled.")
            return
            
        try:
            from core.image_loader import load_sequence
            frames = load_sequence(folder)
            if not frames:
                self.log("No frames found in sequence.")
                return
                
            # Track pixels across all frames
            results = []
            for frame_num, frame in frames:
                frame_results = self.pixel_tracker.track_frame(frame)
                results.append((frame_num, frame_results))
                
            # Export results
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save Comparison Results", "", "CSV Files (*.csv)"
            )
            if output_path:
                self.pixel_tracker.export_to_csv(output_path)
                self.log(f"Exported sequence comparison results to {output_path}")
                
        except Exception as e:
            self.log(f"Error comparing sequence: {str(e)}")
            import traceback
            self.log(traceback.format_exc())

    def compare_across_sims(self):
        """Compare tracked pixels across different simulation folders."""
        if not self.pixel_tracker.coordinates:
            self.log("No pixels being tracked. Please select pixels first.")
            return
            
        # Get reference frame
        ref_path, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Frame", "", "Image Files (*.exr *.png *.jpg *.jpeg)"
        )
        if not ref_path:
            self.log("Simulation comparison cancelled.")
            return
            
        try:
            # Get simulation root directory
            ref_path = Path(ref_path)
            sim_root = ref_path.parent.parent  # Assuming structure: sim_root/sim_XXXX/filename.exr
            
            # Compare across simulations
            results = self.pixel_tracker.compare_across_sims(ref_path)
            
            # Export results
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Save Comparison Results", "", "CSV Files (*.csv)"
            )
            if output_path:
                self.pixel_tracker.export_comparison_to_csv(results, output_path)
                self.log(f"Exported simulation comparison results to {output_path}")
                
        except Exception as e:
            self.log(f"Error comparing simulations: {str(e)}")
            import traceback
            self.log(traceback.format_exc())

    def show_aov_list(self):
        """Show a dialog listing all available AOVs in the current EXR file."""
        if not hasattr(self, 'current_image_path') or not self.current_image_path:
            self.log("Please load an EXR file first")
            return
            
        if not self.current_image_path.lower().endswith('.exr'):
            self.log("Current file is not an EXR file")
            return
            
        try:
            from core.image_loader import get_exr_aovs
            aovs = get_exr_aovs(self.current_image_path)
            if not aovs:
                self.log("No AOVs found in the current EXR file")
                return
                
            # Show dialog with AOV list
            dialog = AOVListDialog(aovs, self)
            dialog.exec_()
            
        except Exception as e:
            self.log(f"Error listing AOVs: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
