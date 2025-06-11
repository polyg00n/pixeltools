"""
main_window.py

Main GUI window for PixelTools — includes dockable log console, buttons for launching 
various tools (dataset analysis, AOV extraction, cleanup, etc.), and connects GUI events 
to core processing functions. Designed with verbose comments to serve as a learning tool.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QLabel, QPushButton, QVBoxLayout,
    QWidget, QTextEdit, QDockWidget, QLineEdit, QHBoxLayout, QInputDialog
)
from PyQt5.QtCore import Qt, QDateTime

# Core functionality modules
from core.analysis import analyze_dataset, print_dataset_stats  # Used in dataset analysis
from core.extractor import extract_aovs_from_sequences  # Used for extracting AOVs from EXR sequences
from core.encoder import encode_sequence  # Encodes image sequences into MP4
from core.thumbnail import create_thumbnail_video  # Assembles thumbnail comparison frames
from core.visualizer import create_aov_comparison  # Builds side-by-side AOV grids from one EXR
from core.cleanup import cleanup_temp_files  # Removes previews, _aov_ folders, temp files

from pathlib import Path
import sys
import io

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel Tracker & Tools")  # Sets the app title

        # --- Top Label and Input Field ---
        self.label = QLabel("Main Tool Panel")  # Title label

        # Input field to specify AOVs for extraction (e.g., 'diffcol,depth')
        self.aov_input = QLineEdit()
        self.aov_input.setPlaceholderText("Enter AOVs (comma-separated)")

        # --- Tool Buttons ---
        self.analyze_button = QPushButton("Analyze Dataset")
        self.analyze_button.clicked.connect(self.run_analysis)

        self.extract_button = QPushButton("Extract AOVs")
        self.extract_button.clicked.connect(self.extract_aovs)

        self.encode_button = QPushButton("Encode Sequence to MP4")
        self.encode_button.clicked.connect(self.encode_video)

        self.thumbnail_button = QPushButton("Create Thumbnail Summary Video")
        self.thumbnail_button.clicked.connect(self.make_thumbnail_video)

        self.compare_button = QPushButton("Create AOV Comparison Grid")
        self.compare_button.clicked.connect(self.compare_aovs)

        self.cleanup_button = QPushButton("Run Cleanup Utilities")
        self.cleanup_button.clicked.connect(self.cleanup_files)

        # --- Organize Buttons and Inputs in Layout ---
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.analyze_button)

        aov_layout = QHBoxLayout()
        aov_layout.addWidget(self.aov_input)
        aov_layout.addWidget(self.extract_button)
        layout.addLayout(aov_layout)

        layout.addWidget(self.encode_button)
        layout.addWidget(self.thumbnail_button)
        layout.addWidget(self.compare_button)
        layout.addWidget(self.cleanup_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)  # Sets main widget as central interface

        # --- Log Console Setup (Dockable) ---
        self.log_console = QTextEdit()  # Multiline text area for log messages
        self.log_console.setReadOnly(True)  # Make log console non-editable
        self.log_console.setLineWrapMode(QTextEdit.NoWrap)  # Preserve line breaks

        self.dock = QDockWidget("Log Console", self)  # Allow docking/moving the log
        self.dock.setWidget(self.log_console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock)

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
        folder = QFileDialog.getExistingDirectory(self, "Select Dataset Folder")
        if not folder:
            self.log("Dataset analysis cancelled.")
            return
        self.log(f"Starting dataset analysis on: {folder}")

        try:
            dataset = analyze_dataset(Path(folder))
            buffer = io.StringIO()
            sys_stdout = sys.stdout
            sys.stdout = buffer
            print_dataset_stats(dataset)
            sys.stdout = sys_stdout
            output = buffer.getvalue()
            buffer.close()
            self.log(output)
        except Exception as e:
            self.log(f"Error during analysis: {e}")

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
        try:
            encode_sequence(Path(folder))
            self.log("Sequence encoded to MP4.")
        except Exception as e:
            self.log(f"Encoding error: {e}")

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
