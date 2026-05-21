import argparse
import json
from pathlib import Path
from typing import Any

from pointcloudlib.dem import process_plot_dem


def _load_config(path: str | None) -> dict[str, Any]:
    if path is None:
        return {}

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("Config must be a JSON object")

    data.pop("config", None)
    return data


def _parse_args() -> argparse.Namespace:
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", default=None)
    pre_args, _ = pre_parser.parse_known_args()

    defaults = _load_config(pre_args.config)

    parser = argparse.ArgumentParser(
        description="Create DEM GeoTIFFs and PNG previews for a plot root."
    )

    parser.add_argument(
        "plot_root",
        nargs="?",
        default=defaults.get("plot_root"),
        help="Plot root folder (e.g., /data/FieldPheno4D/P147)",
    )
    parser.add_argument(
        "--config",
        default=pre_args.config,
        help="Path to a JSON config file with defaults",
    )
    parser.add_argument(
        "--output-dir",
        default="dem",
        help="Output folder name inside plot root (default: dem)",
    )
    parser.add_argument(
        "--dxy",
        type=float,
        default=0.002,
        help="Grid resolution in meters (default: 0.002)",
    )
    parser.add_argument(
        "--max-plane-points",
        type=int,
        default=2_000_000,
        help="Max points used to fit plane (default: 2000000)",
    )
    parser.add_argument(
        "--epsg",
        type=int,
        default=32632,
        help="EPSG code for GeoTIFF (default: 32632)",
    )
    parser.add_argument(
        "--nodata",
        type=float,
        default=-9999.0,
        help="NoData value for GeoTIFF (default: -9999.0)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=13,
        help="Random seed for sampling (default: 13)",
    )
    parser.add_argument(
        "--no-fill-nodata",
        action="store_true",
        help="Disable NoData filling",
    )
    parser.add_argument(
        "--fill-method",
        default="zero_fill",
        choices=["smart_avg", "smart_min", "smart_max", "median_fill", "zero_fill"],
        help="Fill method (default: zero_fill)",
    )
    parser.add_argument(
        "--preview",
        dest="preview",
        action="store_true",
        help="Write PNG previews with a colorful colormap (default: True)",
    )
    parser.add_argument(
        "--no-preview",
        dest="preview",
        action="store_false",
        help="Disable PNG previews",
    )
    parser.set_defaults(preview=True)
    parser.add_argument(
        "--geotiff",
        action="store_true",
        help="Also write GeoTIFF outputs",
    )
    parser.add_argument(
        "--apply-sor",
        dest="apply_sor",
        action="store_true",
        help="Apply Statistical Outlier Removal (SOR)",
    )
    parser.add_argument(
        "--no-apply-sor",
        dest="apply_sor",
        action="store_false",
        help="Disable Statistical Outlier Removal (SOR)",
    )
    parser.set_defaults(apply_sor=defaults.get("apply_sor", False))
    parser.add_argument(
        "--sor-neighbors",
        type=int,
        default=defaults.get("sor_neighbors", 50),
        help="Number of neighbors for SOR (default: 50)",
    )
    parser.add_argument(
        "--sor-std-ratio",
        type=float,
        default=defaults.get("sor_std_ratio", 1.0),
        help="Standard deviation ratio for SOR (default: 1.0)",
    )
    parser.add_argument(
        "--preview-utm",
        action="store_true",
        help="Use UTM coordinates on preview axes (default: local frame)",
    )
    parser.add_argument(
        "--pca-rotate",
        dest="pca_rotate",
        action="store_true",
        help="Rotate in XY using PCA on merged samples (default: True)",
    )
    parser.add_argument(
        "--no-pca-rotate",
        dest="pca_rotate",
        action="store_false",
        help="Disable PCA-based XY rotation",
    )
    parser.set_defaults(pca_rotate=True)
    parser.add_argument(
        "--pca-rotate-max-points",
        type=int,
        default=5_000_000,
        help="Max points for PCA rotation (default: 5000000)",
    )
    parser.add_argument(
        "--bbox-mode",
        default="union",
        choices=["intersection", "union"],
        help="Bounding box mode for cropping (default: union)",
    )
    parser.add_argument(
        "--z-ref",
        default="global-min",
        choices=["global-min", "none"],
        help="Z reference after alignment (default: global-min)",
    )
    parser.add_argument(
        "--z-clip-min",
        type=float,
        default=0.0,
        help="Clip Z below this value (default: 0.0)",
    )
    parser.add_argument(
        "--preview-cmap",
        default="turbo",
        help="Matplotlib colormap for previews (default: turbo)",
    )
    parser.add_argument(
        "--agg",
        default="max",
        choices=["max", "mean", "median"],
        help="Aggregation per cell (default: max)",
    )
    parser.add_argument(
        "--max-grid-cells",
        type=int,
        default=None,
        help="Max grid cells; increases dxy if exceeded",
    )
    parser.add_argument(
        "--dem-max-points",
        type=int,
        default=None,
        help="Max points used per DEM (random sample)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce terminal output",
    )

    parser.set_defaults(**defaults)

    args = parser.parse_args()
    if args.plot_root is None:
        parser.error("plot_root is required (positional or in --config)")

    return args


def main() -> None:
    args = _parse_args()

    process_plot_dem(
        args.plot_root,
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
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
