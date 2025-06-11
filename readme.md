# PixelTools

A Python-based tool for analyzing and processing image sequences, with a focus on pixel-level analysis and visualization.

## Features

- Load and process image sequences (TIFF, PNG, JPEG)
- Pixel-level analysis and tracking
- Interactive GUI for visualization
- Video encoding and thumbnail generation
- Dataset analysis and statistics

## Supported Formats

The tool currently supports the following image formats:
- TIFF (.tif, .tiff)
- PNG (.png)
- JPEG (.jpg, .jpeg)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pixelTools.git
cd pixelTools
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### GUI Mode

Run the application with a graphical user interface:
```bash
python main.py --gui
```

### Command Line Mode

Process image sequences from the command line:
```bash
python main.py --input /path/to/sequences --output /path/to/output
```

## Development

### Project Structure

- `core/`: Core functionality
  - `image_loader.py`: Image loading and processing
  - `encoder.py`: Video encoding
  - `extractor.py`: Feature extraction
  - `visualizer.py`: Visualization tools
  - `analysis.py`: Dataset analysis
- `gui/`: GUI components
  - `main_window.py`: Main application window
  - `image_viewer.py`: Image display widget
  - `pixel_tracker.py`: Pixel tracking interface
- `tests/`: Unit tests

### Adding New Features

1. Create a new branch for your feature
2. Implement the feature
3. Add tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 