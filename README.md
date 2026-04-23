# Imaging Tool Repository

This repository contains two independent project areas:

- `Actuator/pid_simulation`: actuator PID simulation work
- `imaging-suite`: imaging analysis tools and datasets

## Repository Layout

- `Actuator/pid_simulation/`
  - Existing actuator and PID simulation code
- `imaging-suite/`
  - `app.py`: Flask web app for image analysis and camera type detection
  - `templates/index.html`: web UI
  - `image_analyzer_gui.py`: desktop GUI analyzer (tkinter)
  - `jpg_to_pixel_value.py`: JPG pixel extraction utility
  - `pixel_values/`: JSON pixel-stat samples
  - `peak_summary.csv`: summary data

## Quick Start (Imaging Suite)

1. Create/activate a Python virtual environment.
2. Install dependencies:
   - `pip install Flask Pillow numpy scipy`
3. Run the web analyzer:
   - `python imaging-suite/app.py`
4. Open:
   - `http://127.0.0.1:5000`

## Notes

- The imaging tools currently support robust JPG analysis and heuristic camera-type detection (RGB, IR/Thermal, and TOF/depth hints).
- For accurate sensor-level SNR, use RAW12/RAW formats when available.
