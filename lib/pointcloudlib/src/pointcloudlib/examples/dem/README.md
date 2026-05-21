# DEM processing example

This example builds per-date DEM grids from LAS/LAZ point clouds in a plot folder.
It aligns the point clouds to a fitted ground plane, optionally rotates the XY
frame, crops to a shared bounding box, fills NoData holes, and writes PNG previews
(and optionally GeoTIFFs).

Outputs are written under the plot root:
- DEM GeoTIFFs (if enabled): <plot_root>/<output_dir>/*.tif
- PNG previews: <plot_root>/<output_dir>/png/
  - nadir/*.png: per-date XY height previews.
  - bboxes/bboxes_alignment.png: XY bounding boxes after plane alignment (union limits).
  - bboxes/bboxes_pca.png: XY bounding boxes after alignment + PCA rotation (union limits).
  - side_xz/*_side_xz.png: per-date X-Z side view after alignment + PCA (union limits).
  - side_yz/*_side_yz.png: per-date Y-Z side view after alignment + PCA (union limits).

## Usage

Run directly with CLI defaults:

python -m pointcloudlib.examples.dem.process_plot_dem /data/FieldPheno4D/P147

Run using a JSON config file:

python -m pointcloudlib.examples.dem.process_plot_dem --config ./process_plot_dem_config.json

CLI flags override JSON values.

## Config file

See process_plot_dem_config.json for a complete set of configurable settings.
Copy it, edit values, then pass it with --config.

## Parameters

plot_root (str)
  Plot root folder containing LAS/LAZ files. Required unless provided in config.

output_dir (str)
  Output folder name inside plot root.

dxy (float)
  Grid resolution in meters.

max_plane_points (int)
  Max points used to fit the ground plane.

epsg (int)
  EPSG code for GeoTIFF outputs.

nodata (float)
  NoData value used in grids and GeoTIFFs.

seed (int)
  Random seed used when sampling points.

no_fill_nodata (bool)
  If true, skip NoData filling.

fill_method (str)
  Fill method: smart_avg, smart_min, smart_max, median_fill, or zero_fill.
  smart_avg: fills a missing cell by averaging the same cell across other point clouds (mean).
  smart_min: fills a missing cell by taking the minimum value across other point clouds.
  smart_max: fills a missing cell by taking the maximum value across other point clouds.
  median_fill: fills a missing cell by taking the median value across other point clouds.
  zero_fill: fills all missing cells with 0.

preview (bool)
  If true, write PNG previews.

apply_sor (bool)
  If true, applies Statistical Outlier Removal (SOR) directly after reading point clouds to denoise data.

sor_neighbors (int)
  Number of neighbors to consider for SOR (default: 50).

sor_std_ratio (float)
  Standard deviation ratio for SOR outlier detection (default: 1.0).

geotiff (bool)
  If true, write GeoTIFFs.

preview_utm (bool)
  If true, use UTM coordinates on preview axes. Default is local frame.

pca_rotate (bool)
  If true, rotate in XY using PCA on merged samples.

pca_rotate_max_points (int)
  Max points used for PCA-based rotation.

bbox_mode (str)
  Bounding box mode for cropping: intersection or union.

z_ref (str)
  Z reference after alignment: global-min or none.

z_clip_min (float)
  Clip Z values below this threshold after alignment.

preview_cmap (str)
  Matplotlib colormap for PNG previews.

agg (str)
  Per-cell aggregation: max, mean, or median.

max_grid_cells (int or null)
  If set, increases dxy when the grid would exceed this number of cells.

dem_max_points (int or null)
  Max points used per DEM (random sample).

quiet (bool)
  If true, reduce terminal output.
