#!/bin/bash

# Exit on any error
set -e

echo "Setting up FieldPheno4D Website Environment..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Installation complete. To run the server, use:"
echo "source venv/bin/activate"
echo "python app.py"