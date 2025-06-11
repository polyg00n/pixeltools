# PixelTools

**PixelTools** is a modular image sequence analysis toolkit with a GUI and CLI, designed for comparing RGB values across multiple simulations, tracking pixel behavior, exporting features for ML, and visualizing AOV channels from EXR files.

---

## 🚀 Features

- ✅ **Pixel RGB Tracker** with GUI
- ✅ **EXR AOV Extraction** to PNG/JPG
- ✅ **Thumbnail Summary** from multiple sequences
- ✅ **AOV Comparison Grid** for EXR files
- ✅ **CLI Tools for headless workflows**
- ✅ **Export to CSV/NPZ** for ML feature extraction

---

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/pixeltools.git
cd pixeltools

# Install in development mode
pip install -e .
```

Ensure your Python version is 3.8+ and you have OpenEXR and Qt working properly on your OS.

---

## 🖥 Launch the GUI

```bash
pixeltools --gui
```

---

## 🛠 Command Line Tools

```bash
# Analyze dataset
pixeltools --analyze path/to/sequences

# Clean up previews and _aov_* folders
pixeltools --cleanup path/to/sequences

# Extract specific AOVs
pixeltools --extract path/to/sim diffcol normal

# Encode frames to MP4
pixeltools --encode path/to/sim/_aov_diffcol

# Create grid of frame 0 from each sim
pixeltools --thumbnail path/to/simulations

# Compare AOVs in one EXR
pixeltools --compare path/to/frame.exr --aovs diffcol,depth,normal
```

---

## 🧪 Examples

```bash
# Extract 'diffcol' from 500 EXR sequences:
pixeltools --extract ./data/simulations diffcol

# Analyze dataset structure:
pixeltools --analyze ./data/simulations
```

---

## 🧰 ImageMagick Tips

Use ImageMagick separately for quick command-line image diagnostics:

```bash
# View a pixel color
identify -verbose frame.0025.exr | grep Pixel

# Compare two frames visually
compare frame.0025.exr frame.0026.exr diff.png

# Resize EXR to PNG for fast viewing
convert frame.0050.exr -resize 50% frame_thumb.png
```

---

## 🧱 Project Layout

```bash
pixeltools/
├── gui/              # PyQt GUI files
├── core/             # Image, pixel, export tools
├── tests/            # Unit tests
├── data/             # Optional sample data/output folders
├── main.py           # CLI/GUI launcher
├── setup.py
├── README.md
```

---

## 📖 License

MIT License. Attribution appreciated. Built to support visual ML workflows, dataset debugging, and technical art pipelines.

---

## ✨ Maintainer

Sergio Gonzalez — pull requests welcome!
