# FieldPheno4D Dataset

> **Note:** The included web-based interactive viewer is currently **under construction**.

## Overview
**FieldPheno4D** is a dataset containing high-quality and multitemporal 3D point clouds of multiple crops captured in the field using a robotic field robot. 

The dataset was gathered using a custom **Field Robot for High-throughput and High-resolution 3D Plant Phenotyping**. This robotic platform is equipped with two industrial-grade laser triangulation scanners and a highly-accurate georeferencing system to enable multi-temporal 3D reconstruction in agricultural fields, supporting the estimation of phenotypic traits such as leaf area, leaf angle, and plant height. You can find more detailed information about the robotic platform in our paper: [DOI](https://doi.org/10.1109/MRA.2023.3321402). The dateset was created in 2023 on the Phenorob experimental field at Campus Kleinaltendorf, next to Bonn, Germany.

## Dataset Visualization
Below is an **animated .gif demo** showing the multitemporal changes of the single crop plot 147 from the dataset including multiple corn plants. Each point cloud is georeferenced with centimeter accuracy and ICP fine-registered over time to ensure a temporal alignment. More crop plots will be added in the future.

![Temporal Slider Demo](demo_slider.gif)

## Local Website Viewer

The repository also includes a web application to interactively browse different crop plots (PXXX) and view nadir and side views of the 3D point clouds across a temporal slider.

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