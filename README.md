# FieldPheno4D dataset Website

## Overview
**FieldPheno4D dataset**: High-quality and Multitemporal 3D point clouds of Multiple Crops captured in the field.

This web application provides an interactive viewer for the FieldPheno4D dataset. It allows users to browse different crop plots (PXXX) and view nadir images of 3D point clouds across a temporal slider corresponding to the recording dates.

## Features
- **Plot Selection Tabs**: Easily switch between available agricultural plots.
- **Temporal Slider**: Navigate through time using discrete sampling dates.
- **Image Visualization**: Real-time display of nadir-view generated from the point cloud for the selected date.
- **Light/Dark Mode**: An integrated toggle for comfortable viewing across different lighting conditions.

## Project Structure
- `app.py`: Flask backend serving the metadata and static views.
- `templates/`: HTML templates for the frontend.
- `static/`: CSS and JavaScript files for interactivity and styling.
- `/data/FieldPheno4D/`: Target directory for the dataset (expected format: `/data/FieldPheno4D/<plot_id>/<date>/image.png`).

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