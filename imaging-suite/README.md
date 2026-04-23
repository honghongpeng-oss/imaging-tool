# Imaging Suite

This folder contains all imaging-related utilities, data samples, and UI tools.

## Contents

- `app.py`: Flask web analyzer with image stats and camera-type detection
- `templates/index.html`: frontend for upload and visualization
- `image_analyzer_gui.py`: desktop tkinter GUI analyzer
- `jpg_to_pixel_value.py`: script for JPG pixel-value extraction
- `pixel_values/`: sample JSON outputs
- `peak_summary.csv`: summary CSV data

## Run Web Analyzer

```bash
python app.py
```

Then open `http://127.0.0.1:5000`.

## Install Dependencies

```bash
pip install Flask Pillow numpy scipy
```

## Scope

- RGB image stats
- JPG-relative noise and SNR estimates
- Heuristic camera-type detection for RGB, IR/thermal, and TOF/depth images
