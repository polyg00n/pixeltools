"""
image_viewer.py

A widget for displaying images with pixel coordinate tracking and hover effects.
"""

import logging
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageViewer(QWidget):
    """Widget for displaying images with pixel coordinate tracking."""
    
    # Signals for pixel interaction
    pixel_clicked = pyqtSignal(int, int)  # x, y coordinates
    pixel_hovered = pyqtSignal(int, int)  # x, y coordinates
    
    def __init__(self):
        super().__init__()
        self.current_image = None
        self.current_pixmap = None
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        layout.addWidget(self.image_label)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        self.image_label.setMouseTracking(True)
    
    def set_image(self, image_data):
        """Set the current image to display.
        
        Args:
            image_data: numpy array of shape (height, width, channels)
        """
        try:
            if image_data is None:
                self.clear()
                return
                
            # Convert numpy array to QImage
            height, width = image_data.shape[:2]
            if image_data.ndim == 2:  # Grayscale
                bytes_per_line = width
                qimage = QImage(image_data.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            else:  # RGB/RGBA
                bytes_per_line = width * image_data.shape[2]
                qimage = QImage(image_data.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # Convert to QPixmap and scale to fit
            self.current_pixmap = QPixmap.fromImage(qimage)
            self.current_image = image_data
            self.update_display()
            
        except Exception as e:
            logger.error(f"Error setting image: {str(e)}")
            self.clear()
    
    def update_display(self):
        """Update the display with the current pixmap."""
        if self.current_pixmap:
            # Scale pixmap to fit the label while maintaining aspect ratio
            scaled_pixmap = self.current_pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
    
    def clear(self):
        """Clear the current image."""
        self.current_image = None
        self.current_pixmap = None
        self.image_label.clear()
    
    def resizeEvent(self, event):
        """Handle widget resize events."""
        super().resizeEvent(event)
        self.update_display()
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if self.current_image is None:
            return
            
        # Get click position relative to the image
        pos = event.pos()
        label_pos = self.image_label.mapFrom(self, pos)
        
        # Calculate image coordinates
        if self.current_pixmap:
            # Get the actual displayed image size
            displayed_size = self.image_label.pixmap().size()
            # Calculate scaling factors
            scale_x = self.current_image.shape[1] / displayed_size.width()
            scale_y = self.current_image.shape[0] / displayed_size.height()
            
            # Convert to image coordinates
            x = int(label_pos.x() * scale_x)
            y = int(label_pos.y() * scale_y)
            
            # Ensure coordinates are within bounds
            if 0 <= x < self.current_image.shape[1] and 0 <= y < self.current_image.shape[0]:
                self.pixel_clicked.emit(x, y)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.current_image is None:
            return
            
        # Get hover position relative to the image
        pos = event.pos()
        label_pos = self.image_label.mapFrom(self, pos)
        
        # Calculate image coordinates
        if self.current_pixmap:
            # Get the actual displayed image size
            displayed_size = self.image_label.pixmap().size()
            # Calculate scaling factors
            scale_x = self.current_image.shape[1] / displayed_size.width()
            scale_y = self.current_image.shape[0] / displayed_size.height()
            
            # Convert to image coordinates
            x = int(label_pos.x() * scale_x)
            y = int(label_pos.y() * scale_y)
            
            # Ensure coordinates are within bounds
            if 0 <= x < self.current_image.shape[1] and 0 <= y < self.current_image.shape[0]:
                self.pixel_hovered.emit(x, y)