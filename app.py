import os
from flask import Flask, render_template, jsonify, send_from_directory

app = Flask(__name__)

# Base directory for the dataset
DATA_DIR = '/data/FieldPheno4D'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/plots')
def get_plots():
    """
    Returns a structured dictionary of available plots and their associated dates.
    Expects structure: /data/FieldPheno4D/PXXX/date1_nadir.png
    """
    data = {}
    if not os.path.exists(DATA_DIR):
        # Mock data for demonstration purposes if directory does not exist
        return jsonify({
            "P001": ["2023-05-01", "2023-05-15", "2023-06-01"],
            "P002": ["2023-05-02", "2023-05-16", "2023-06-02"]
        })

    # Prefer a global 'combined' directory: /data/FieldPheno4D/combined/*.png
    global_combined = os.path.join(DATA_DIR, 'combined')
    if os.path.exists(global_combined) and os.path.isdir(global_combined):
        for file in os.listdir(global_combined):
            if file.endswith('.png'):
                plot = os.path.splitext(file)[0]
                data[plot] = ["combined"]
        if data:
            return jsonify(data)

    # Otherwise, inspect each plot directory for combined images or the legacy nadir structure
    for plot in os.listdir(DATA_DIR):
        plot_path = os.path.join(DATA_DIR, plot)
        if not os.path.isdir(plot_path):
            continue

        # 1) Check for a per-plot combined file: /data/FieldPheno4D/PXXX/combined.png
        combined_file = os.path.join(plot_path, 'combined.png')
        if os.path.exists(combined_file):
            data[plot] = ["combined"]
            continue

        # 2) Check for per-plot combined directories:
        #    - /data/FieldPheno4D/PXXX/combined/*.png
        #    - /data/FieldPheno4D/PXXX/dem/png/combined/*.png
        combined_dirs = [
            os.path.join(plot_path, 'combined'),
            os.path.join(plot_path, 'dem', 'png', 'combined')
        ]
        imgs = []
        for cdir in combined_dirs:
            if os.path.exists(cdir) and os.path.isdir(cdir):
                imgs = [f for f in os.listdir(cdir) if f.endswith('.png')]
                if imgs:
                    break

        if imgs:
            labels = []
            for f in imgs:
                name = os.path.splitext(f)[0]
                if name.endswith('_combined'):
                    name = name.rsplit('_', 1)[0]
                labels.append(name)
            data[plot] = sorted(labels)
            continue

        # 3) Fallback to legacy nadir images: /data/FieldPheno4D/PXXX/dem/png/nadir/*.png
        dates = []
        nadir_dir = os.path.join(plot_path, 'dem', 'png', 'nadir')
        if os.path.exists(nadir_dir) and os.path.isdir(nadir_dir):
            for file in os.listdir(nadir_dir):
                if file.endswith('.png'):
                    date_str = os.path.splitext(file)[0]
                    if date_str not in dates:
                        dates.append(date_str)
        if dates:
            data[plot] = sorted(dates)

    return jsonify(data)

@app.route('/data/<path:filename>')
def serve_image(filename):
    return send_from_directory(DATA_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)