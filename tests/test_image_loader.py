"""
test_image_loader.py

Unit tests for image_loader.py using test images or mocks.
"""

import unittest
from core import image_loader
from pathlib import Path
import numpy as np
import os

class TestImageLoader(unittest.TestCase):

    def test_load_png_image(self):
        sample_path = Path("data/samples/sample.png")
        if not sample_path.exists():
            self.skipTest("sample.png not found")
        image = image_loader.load_image(sample_path)
        self.assertEqual(len(image.shape), 3)
        self.assertEqual(image.shape[2], 3)
        self.assertTrue(np.max(image) <= 255)

    def test_load_exr_without_aov(self):
        sample_path = Path("data/samples/sample.exr")
        if not sample_path.exists():
            self.skipTest("sample.exr not found")
        image = image_loader.load_image(sample_path)
        self.assertIsNotNone(image)

if __name__ == '__main__':
    unittest.main()
