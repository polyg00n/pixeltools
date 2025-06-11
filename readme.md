# Pixel Comparison GUI for AOV Sequences

This project provides a powerful, user-friendly GUI tool built with PyQt5 to analyze and compare pixel color values across multiple sequences of rendered images. It is designed specifically for workflows that involve synthetic data generation and machine learning pipelines, especially in visual effects, simulation, and computer vision.

---

## 🎯 Purpose

When rendering simulations or creating synthetic datasets, it's often useful to:

* Track pixel values across time or different simulation settings
* Identify if certain pixels (or regions) change over time or remain static
* Use pixel color stability or variation as features for machine learning

This tool allows users to:

* Load multiple image sequences (EXR, PNG, JPG)
* View individual AOVs (Arbitrary Output Variables) in EXR files
* Select specific pixel coordinates interactively
* Compare RGB values of selected pixels across all frames and sequences
* Export this data for ML training or dataset analysis

---

## 🖥️ Features

* ✅ Multi-sequence loader
* ✅ AOV selector for EXR files (e.g., `diffcol`, `depth`, `normal`, etc.)
* ✅ Interactive pixel selection via mouse clicks
* ✅ Frame-by-frame viewer with slider
* ✅ Visual display of pixel selections
* ✅ Categorical flag: changed/not changed (based on a color tolerance threshold)
* ✅ CSV + NPZ export of RGB data and delta comparisons

---

## 🔧 Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/pixel-tracker-gui.git
cd pixel-tracker-gui
```

2. Create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the app:

```bash
python main.py
```

---

## 🧪 Usage Instructions

### 1. Load Sequences

* Click **"Load Folder of Sequences"**
* Select a directory that contains EXR, PNG, or JPG image sequences
* Files should follow this naming format: `name.####.exr` (e.g., `clothsimv1.0023.exr`)

### 2. Select AOV

* The AOV dropdown will auto-populate based on EXR channels
* Select an AOV (e.g., `diffcol`) to analyze a specific render pass

### 3. Navigate Frames

* Use the slider to scrub through the sequence
* The currently displayed frame will update accordingly

### 4. Select Pixels

* Click on the image to record the coordinates of the pixel you want to track
* Multiple pixels can be selected and will be listed in the GUI

### 5. Export Data

* Click "Export Comparison Data" to generate:

  * `comparison_export.csv` – frame-by-frame RGB values and change flags
  * `comparison_export.npz` – structured NumPy data for ML pipelines

---

## 💼 Potential Use Cases

### Machine Learning Feature Extraction

* Use RGB stability of pixels over time as binary or continuous features
* Segment stable vs unstable regions to guide training sample selection

### Simulation Consistency Checks

* Ensure that simulations under identical conditions produce consistent image outputs

### Visual Debugging of AOVs

* Track how lighting, shading, or cloth deformation affects specific pixels

### Synthetic Data Quality Audits

* Detect artifacts or noise in generated sequences

---

## 🛠 ImageMagick Alternatives (CLI Examples)

Even without this GUI, you can perform many useful tasks using [ImageMagick](https://imagemagick.org):

### 1. 🔍 Compare Two Frames

```bash
compare -metric RMSE frame_0001.exr frame_0002.exr diff.png
```

* Outputs root mean square error and a visual difference image.

### 2. 🎨 Extract a Pixel Color

```bash
convert input.exr -crop 1x1+X+Y txt:
```

* Replace `X` and `Y` with pixel coordinates.
* Outputs the RGB value at that location.

### 3. 📊 Batch Pixel Differences (bash loop)

```bash
for i in {0001..0500}; do
  convert sim1.$i.exr -crop 1x1+128+256 txt: >> sim1_pixel_values.txt
  convert sim2.$i.exr -crop 1x1+128+256 txt: >> sim2_pixel_values.txt
done
```

### 4. 🧯 Highlight Differences

```bash
compare -fuzz 5% -metric AE imageA.exr imageB.exr diff_output.exr
```

* `-fuzz 5%` adds tolerance.
* `AE` counts the number of different pixels.

### 5. 🧪 Extract Channels

```bash
convert input.exr -channel R -separate red.exr
```

* You can then perform analysis on individual AOV channels.

---

## 🧠 Tips for Extending This Project

* Add **region-based tracking** (patches instead of single pixels)
* Integrate **SQLite or Pandas** for advanced data querying
* Export heatmaps or timelines of pixel change intensity
* Enable **headless mode** (CLI-only comparison for HPC pipelines)
* Add **AI-driven anomaly detection** on pixel sequences

---

## 📂 Repository Structure

```bash
pixel-tracker-gui/
├── main.py                # Main GUI logic
├── requirements.txt       # Python dependencies
├── comparison_export.csv  # Sample output
├── comparison_export.npz  # NumPy structured array
└── README.md              # This file
```

---

## 🧾 License

MIT License. Feel free to use, extend, or contribute back!

---

## 🤝 Acknowledgments

* [OpenEXR](https://www.openexr.com/) for deep image support
* [PyQt5](https://riverbankcomputing.com/software/pyqt/) for GUI framework
* [ImageMagick](https://imagemagick.org) for being an incredible CLI tool

---

## 📫 Contact

For bugs, questions, or contributions, please contact: `your.email@example.com` or open an issue on GitHub.
