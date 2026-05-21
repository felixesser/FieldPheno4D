from __future__ import annotations

import argparse
import csv
from pathlib import Path

from flask import Flask, jsonify, render_template, send_from_directory
from markupsafe import Markup


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _data_dir_candidates() -> list[Path]:
    repo_root = _repo_root()
    return [
        repo_root / "data" / "FieldPheno4Dimg",
        Path("/mnt/d/FieldPheno4Dimg"),
        repo_root / "data" / "FieldPheno4D",
        Path("/mnt/d/FieldPheno4D"),
    ]


def _resolve_data_dir() -> Path:
    for candidate in _data_dir_candidates():
        if candidate.exists():
            return candidate
    return _data_dir_candidates()[0]


def _load_download_links() -> dict[str, dict[str, str]]:
    csv_path = Path(__file__).resolve().parent / "bonndatalinks.csv"
    links: dict[str, dict[str, str]] = {}
    try:
        if csv_path.exists():
            with csv_path.open(newline="", encoding="utf-8") as handle:
                reader = csv.reader(handle)
                for row in reader:
                    if len(row) < 2:
                        continue
                    plot = row[0].strip()
                    url = row[1].strip()
                    species = row[2].strip() if len(row) > 2 else ""
                    if plot:
                        links[plot] = {"url": url, "species": species}
    except Exception:
        return {}
    return links


def _load_text_html(filename: str) -> Markup:
    text_path = Path(__file__).resolve().parent / "texts" / filename
    html = ""
    try:
        if text_path.exists():
            raw_text = text_path.read_text(encoding="utf-8").strip()
            if raw_text:
                paragraphs = [f"<p>{paragraph.strip()}</p>" for paragraph in raw_text.split("\n\n") if paragraph.strip()]
                html = Markup("\n".join(paragraphs))
    except Exception:
        html = ""
    return html


def _load_title_text() -> str:
    title_path = Path(__file__).resolve().parent / "texts" / "title.txt"
    title_text = "FieldPheno4D Dataset"
    try:
        if title_path.exists():
            raw_title = title_path.read_text(encoding="utf-8").strip()
            if raw_title:
                title_text = raw_title
    except Exception:
        pass
    return title_text


def _build_plots_data() -> dict[str, list[str]]:
    data: dict[str, list[str]] = {}
    data_dir = _resolve_data_dir()
    if not data_dir.exists():
        return {
            "P001": ["2023-05-01", "2023-05-15", "2023-06-01"],
            "P002": ["2023-05-02", "2023-05-16", "2023-06-02"],
        }

    global_combined = data_dir / "combined"
    if global_combined.is_dir():
        for file in sorted(global_combined.iterdir()):
            if file.suffix.lower() == ".png":
                data[file.stem] = ["combined"]
        if data:
            return data

    for plot_dir in sorted(data_dir.iterdir()):
        if not plot_dir.is_dir():
            continue

        combined_file = plot_dir / "combined.png"
        if combined_file.exists():
            data[plot_dir.name] = ["combined"]
            continue

        combined_dirs = [
            plot_dir / "combined",
            plot_dir / "dem" / "png" / "combined",
        ]
        labels: list[str] = []
        for combined_dir in combined_dirs:
            if combined_dir.is_dir():
                labels = [
                    file.stem.removesuffix("_combined")
                    for file in sorted(combined_dir.iterdir())
                    if file.suffix.lower() == ".png"
                ]
                if labels:
                    break
        if labels:
            data[plot_dir.name] = sorted(labels)
            continue

        nadir_dir = plot_dir / "dem" / "png" / "nadir"
        if nadir_dir.is_dir():
            dates = [file.stem for file in sorted(nadir_dir.iterdir()) if file.suffix.lower() == ".png"]
            if dates:
                data[plot_dir.name] = sorted(dates)

    return data


def _build_page_context(*, asset_base: str, data_base: str) -> dict[str, object]:
    return {
        "asset_base": asset_base.rstrip("/"),
        "data_base": data_base.rstrip("/"),
        "description": _load_text_html("description.txt"),
        "title": _load_title_text(),
        "acknowledgments": _load_text_html("acknowledgments.txt"),
        "download_links": _load_download_links(),
        "plots_data": _build_plots_data(),
    }


template_folder = str(Path(__file__).resolve().parent / "templates")
static_folder = str(Path(__file__).resolve().parent / "static")
app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)


@app.route("/")
def index():
    context = _build_page_context(asset_base="/static", data_base="/data")
    return render_template("index.html", **context)


@app.route("/api/plots")
def get_plots():
    """Return available plots and temporal labels for the viewer."""
    return jsonify(_build_plots_data())


@app.route("/data/<path:filename>")
def serve_image(filename):
    return send_from_directory(_resolve_data_dir(), filename)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the FieldPheno4D viewer website.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    app.run(debug=args.debug, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
