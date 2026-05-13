# FieldPheno4D Dataset

> **Note:** The included web-based interactive viewer is currently **under construction**.

## Overview
**FieldPheno4D** is a dataset containing high-quality and multitemporal 3D point clouds of multiple crops captured directly in the field. 

The dataset was gathered using a custom **Field Robot for High-throughput and High-resolution 3D Plant Phenotyping**. This robotic platform is equipped with multiple laser and camera sensors to enable in-field plant scanning. It allows for the creation of digital twins of plants through accurate 3D reconstruction, supporting the estimation of phenotypic traits such as leaf area, leaf angle, and plant height. You can find more detailed information about the robotic platform in our paper: [arXiv:2310.11516](https://arxiv.org/abs/2310.11516).

## Dataset Visualization
While an interactive viewer script is included in this repository, GitHub's markdown file rendering does not natively support interactive HTML/JavaScript sliders. Below is an **animated demo** showing the multitemporal changes of crop plots from the dataset (plot P147): 

![Temporal Slider Demo](demo_slider.gif)

## Local Website Viewer

The repository also includes a Flask-based web application to interactively browse different crop plots (PXXX) and view nadir images of 3D point clouds across a temporal slider.

### Project Structure
- `app.py`: Flask backend serving the metadata and static views.
- `templates/`: HTML templates for the frontend.
- `static/`: CSS and JavaScript files for interactivity and styling.
- `./data/FieldPheno4D/`: Target directory for the dataset (expected format: `./data/FieldPheno4D/<plot_id>/<date>/image.png`).

## Installation

Run the provided installation script to create a virtual environment and install the required dependencies:

```bash
./installation.sh
```

## Running the Application

1. Activate the environment:
```bash
source venv/bin/activate
```
2. Start the flask application:
```bash
python app.py
```
3. Open `http://localhost:5000` in your browser.