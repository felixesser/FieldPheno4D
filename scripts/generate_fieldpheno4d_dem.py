from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _pointcloudlib_src() -> Path:
    return _repo_root() / "lib" / "pointcloudlib" / "src"


def _ensure_pointcloudlib_on_path() -> None:
    src_dir = _pointcloudlib_src()
    if not src_dir.exists():
        raise FileNotFoundError(
            f"pointcloudlib source tree not found at {src_dir}. "
            "Clone the submodule first."
        )

    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)


def _has_pointcloud_files(path: Path) -> bool:
    return any(path.rglob("*.las")) or any(path.rglob("*.laz"))


def _discover_plot_roots(dataset_root: Path, selected_plots: list[str] | None) -> list[Path]:
    if selected_plots:
        return [dataset_root / plot_name for plot_name in selected_plots]

    if _has_pointcloud_files(dataset_root):
        return [dataset_root]

    plot_roots = [
        child
        for child in sorted(dataset_root.iterdir())
        if child.is_dir() and _has_pointcloud_files(child)
    ]
    return plot_roots


def _plot_label(plot_root: Path) -> str:
    for part in reversed(plot_root.parts):
        if re.fullmatch(r"P\d+", part):
            return part
    return plot_root.name


def _mirror_output(plot_root: Path, output_root: Path, output_dir_name: str) -> Path:
    label = _plot_label(plot_root)
    if output_root == plot_root.parent:
        return plot_root / output_dir_name
    source_dir = plot_root / output_dir_name
    target_dir = output_root / label / output_dir_name
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
    return target_dir


def _load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}

    with open(config_path, "r", encoding="utf8") as fh:
        loaded = json.load(fh)
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file must contain a JSON object: {config_path}")
    return loaded


def _build_parser(config: dict | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate FieldPheno4D DEM preview images using pointcloudlib."
    )
    parser.add_argument(
        "dataset_root",
        nargs="?",
        default=(config.get("dataset_root") if config else "data/FieldPheno4D"),
        help="Root folder containing FieldPheno4D plot folders.",
    )
    parser.add_argument(
        "--output-root",
        default=(config.get("output_root") if config else "data/FieldPheno4Dimg"),
        help="Mirror generated previews into this folder.",
    )
    parser.add_argument(
        "--pointcloud-output-root",
        default=(config.get("pointcloud_output_root") if config else None),
        help="Mirror rewritten LAS/LAZ files into this folder; defaults to in-place overwrite.",
    )
    parser.add_argument(
        "--plots",
        nargs="*",
        default=None,
        help="Optional plot names to process, e.g. P146 P147.",
    )
    parser.add_argument("--output-dir", default=(config.get("output_dir") if config else "dem"), help="Preview output folder name.")
    parser.add_argument("--dxy", type=float, default=(config.get("dxy") if config else 0.002), help="Grid resolution in meters.")
    parser.add_argument(
        "--max-plane-points",
        type=int,
        default=(config.get("max_plane_points") if config else 2_000_000),
        help="Max points used to fit the reference plane.",
    )
    parser.add_argument("--epsg", type=int, default=(config.get("epsg") if config else 32632), help="EPSG code for GeoTIFF outputs.")
    parser.add_argument("--nodata", type=float, default=(config.get("nodata") if config else -9999.0), help="NoData value.")
    parser.add_argument("--seed", type=int, default=(config.get("seed") if config else 13), help="Random seed.")
    parser.add_argument(
        "--no-fill-nodata",
        action="store_true",
        help="Disable NoData filling before rendering.",
    )
    parser.add_argument(
        "--fill-method",
        default="zero_fill",
        choices=["smart_avg", "smart_min", "smart_max", "median_fill", "zero_fill"],
        help="NoData fill strategy.",
    )
    parser.add_argument("--preview", dest="preview", action="store_true", help="Write PNG previews.")
    parser.add_argument("--no-preview", dest="preview", action="store_false", help="Skip PNG previews.")
    parser.set_defaults(preview=(config.get("preview") if config else True))
    parser.add_argument("--geotiff", action="store_true", help="Also write GeoTIFF outputs.")
    parser.add_argument(
        "--apply-sor",
        dest="apply_sor",
        action="store_true",
        help="Apply Statistical Outlier Removal.",
    )
    parser.add_argument(
        "--no-apply-sor",
        dest="apply_sor",
        action="store_false",
        help="Disable Statistical Outlier Removal.",
    )
    parser.set_defaults(apply_sor=(config.get("apply_sor") if config else False))
    parser.add_argument("--sor-neighbors", type=int, default=50, help="SOR neighbors.")
    parser.add_argument("--sor-std-ratio", type=float, default=1.0, help="SOR standard deviation ratio.")
    parser.add_argument("--preview-utm", action="store_true", help="Render previews in UTM coordinates.")
    parser.add_argument("--pca-rotate", dest="pca_rotate", action="store_true", help="Enable XY PCA rotation.")
    parser.add_argument("--no-pca-rotate", dest="pca_rotate", action="store_false", help="Disable XY PCA rotation.")
    parser.set_defaults(pca_rotate=(config.get("pca_rotate") if config else True))
    parser.add_argument(
        "--pca-rotate-max-points",
        type=int,
        default=(config.get("pca_rotate_max_points") if config else 5_000_000),
        help="Max points used for PCA rotation.",
    )
    parser.add_argument(
        "--bbox-mode",
        default="union",
        choices=["intersection", "union"],
        help="Bounding box mode.",
    )
    parser.add_argument(
        "--z-ref",
        default=(config.get("z_ref") if config else "global-min"),
        choices=["global-min", "none"],
        help="Z reference mode.",
    )
    parser.add_argument("--z-clip-min", type=float, default=0.0, help="Clip Z below this threshold.")
    parser.add_argument("--preview-cmap", default=(config.get("preview_cmap") if config else "turbo"), help="Matplotlib colormap for previews.")
    parser.add_argument("--agg", default=(config.get("agg") if config else "max"), choices=["max", "mean", "median"], help="Cell aggregation.")
    parser.add_argument("--max-grid-cells", type=int, default=(config.get("max_grid_cells") if config else None), help="Increase dxy if the grid becomes too large.")
    parser.add_argument("--dem-max-points", type=int, default=(config.get("dem_max_points") if config else None), help="Max points sampled per DEM.")
    parser.add_argument("--quiet", action="store_true", help="Reduce console output.")
    parser.add_argument(
        "--config",
        default=(config.get("config_path") if config else "scripts/process_plot_dem_config.json"),
        help="Path to JSON config file with default parameters.",
    )
    parser.add_argument(
        "--write-pointclouds",
        dest="write_pointclouds",
        action="store_true",
        help="Write transformed height values back to the source LAS/LAZ files.",
    )
    parser.add_argument(
        "--no-write-pointclouds",
        dest="write_pointclouds",
        action="store_false",
        help="Skip writing transformed height values back to the source LAS/LAZ files.",
    )
    parser.set_defaults(write_pointclouds=(config.get("write_pointclouds") if config else False))
    return parser


def _iter_plot_roots(dataset_root: Path, selected_plots: list[str] | None) -> Iterable[Path]:
    for plot_root in _discover_plot_roots(dataset_root, selected_plots):
        if plot_root.exists() and plot_root.is_dir():
            yield plot_root


def main() -> int:
    default_config_path = Path(__file__).resolve().parents[1] / "scripts" / "process_plot_dem_config.json"
    config_probe = argparse.ArgumentParser(add_help=False)
    config_probe.add_argument("--config", default=str(default_config_path))
    parsed_probe, _ = config_probe.parse_known_args()

    config_path = Path(parsed_probe.config).expanduser().resolve()
    config = _load_config(config_path)
    config.setdefault("config_path", str(config_path))

    parser = _build_parser(config)
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root).resolve()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    _ensure_pointcloudlib_on_path()
    from pointcloudlib.dem import process_plot_dem  # type: ignore[import-not-found]

    plot_roots = list(_iter_plot_roots(dataset_root, args.plots))
    if not plot_roots:
        parser.error(f"No plot folders with LAS/LAZ files found under {dataset_root}")

    for plot_root in plot_roots:
        print(f"[INFO] Processing {plot_root.name} from {plot_root}")
        process_plot_dem(
            plot_root,
            output_dir_name=args.output_dir,
            dxy=args.dxy,
            max_plane_points=args.max_plane_points,
            epsg=args.epsg,
            nodata=args.nodata,
            seed=args.seed,
            agg=args.agg,
            max_grid_cells=args.max_grid_cells,
            dem_max_points=args.dem_max_points,
            fill_nodata=not args.no_fill_nodata,
            fill_method=args.fill_method,
            write_preview=args.preview,
            write_geotiff=args.geotiff,
            preview_cmap=args.preview_cmap,
            preview_local_frame=not args.preview_utm,
            pca_rotate_xy=args.pca_rotate,
            pca_rotate_max_points=args.pca_rotate_max_points,
            bbox_mode=args.bbox_mode,
            z_ref_mode=args.z_ref,
            z_clip_min=args.z_clip_min,
            apply_sor=args.apply_sor,
            sor_neighbors=args.sor_neighbors,
            sor_std_ratio=args.sor_std_ratio,
            write_pointclouds=args.write_pointclouds,
            height_scalarfield_name=config.get("height_scalarfield_name", "height"),
            pointcloud_output_root=args.pointcloud_output_root,
            verbose=not args.quiet,
        )
        mirrored_dir = _mirror_output(plot_root, output_root, args.output_dir)
        print(f"[INFO] Mirrored previews to {mirrored_dir}")

    print("[INFO] FieldPheno4D DEM generation complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())