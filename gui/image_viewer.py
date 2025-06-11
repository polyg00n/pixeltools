"""
image_viewer.py

Handles displaying image sequences in the GUI, supports zooming, panning,
and pixel picking. This will integrate with pixel_tracker.py to track values.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

class ImageViewer(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(True)
        self.setMouseTracking(True)
        self.image_data = None  # Store the image as NumPy array if needed
        self.pixel_callback = None  # Set this to trigger logic on pixel click

    def display_image(self, image):
        """
        Accepts a NumPy image and converts it to QImage/QPixmap for display.
        """
        self.image_data = image
        height, width, channels = image.shape
        qimg = QImage(image.data, width, height, width * channels, QImage.Format_RGB888).rgbSwapped()
        self.setPixmap(QPixmap.fromImage(qimg))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.image_data is not None:
            x = int(event.x() * self.image_data.shape[1] / self.width())
            y = int(event.y() * self.image_data.shape[0] / self.height())
            if self.pixel_callback:
                self.pixel_callback(x, y)

    def set_pixel_callback(self, callback):
        """
        Connect a function to receive (x, y) pixel coordinates.
        """
        self.pixel_callback = callback