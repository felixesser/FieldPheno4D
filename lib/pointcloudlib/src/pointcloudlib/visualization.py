"""
Visualization extensions for PointCloud class.
"""

from enum import Enum
import pyvista as pv
import matplotlib.cm as cm
import numpy as np
import open3d as o3d
from pointcloudlib import PointCloud
import matplotlib.pyplot as plt


class Visualization:
    """Visualization methods for PointCloud class.

    Non-static methods are attached to the PointCloud class (see __init__.py).
    """  # noqa: E501

    def cloud_2_gif(
        self, sc_field: str, cmap: str = "viridis", fname: str = ""
    ) -> None:
        """Create a GIF animation of the point cloud rotating around its center.

        Args:
            sc_field (str): Scalar field to visualize.
            cmap (str, optional): Colormap to use. Defaults to "viridis".
            fname (str, optional): Filename for the output GIF. Defaults to "".
        """  # noqa: E501

        cloud = pv.PolyData(self.xyz)

        pl = pv.Plotter(off_screen=True, image_scale=1)
        pl.add_mesh(
            cloud,
            style="points",
            render_points_as_spheres=False,
            emissive=False,
            color="#cb3b1b",
            scalars=self.scalarfields[sc_field],
            cmap=cmap,
            opacity=1.0,
            point_size=3.0,
            show_scalar_bar=False,
            scalar_bar_args={"title": sc_field + " [m]", "vertical": True},
        )

        pl.background_color = "#FFFFFF"
        pl.enable_eye_dome_lighting()
        pl.show(auto_close=False)

        viewup = [0, 0, 1]

        path = pl.generate_orbital_path(
            n_points=120, shift=cloud.length, viewup=viewup, factor=3.0
        )

        pl.open_gif(fname)
        pl.orbit_on_path(
            path, write_frames=True, viewup=viewup, progress_bar=True, step=0.1
        )
        pl.close()

        return

    class Color(Enum):
        """Color modes for point cloud visualization

        Args:
            Enum: Enumeration base class
        """

        Intensity = 1
        Height = 2
        ScalarField = 3
        Custom = 4

    def plot(self, scalarfield: str = None) -> None:
        """Plot the point cloud using Open3D.

        Args:
            scalarfield (str, optional): String for the visualization color.
                                         Defaults to None.
        """

        point_cloud = o3d.geometry.PointCloud()
        point_cloud.points = o3d.utility.Vector3dVector(self.xyz - self.txyz)

        if scalarfield is None:
            z_min, z_max = np.min(self.xyz[:, 2]), np.max(self.xyz[:, 2])
            z_normalized = (self.xyz[:, 2] - z_min) / (z_max - z_min)
            colors = cm.viridis(z_normalized)[:, :3]
            point_cloud.colors = o3d.utility.Vector3dVector(colors)

        elif scalarfield == "M3C2distance":
            z_min = np.min(self.scalarfields["M3C2distance"])
            z_max = np.max(self.scalarfields["M3C2distance"])
            z_normalized = (self.scalarfields["M3C2distance"] - z_min) / (
                z_max - z_min
            )
            colors = cm.viridis(z_normalized)[:, :3]
            point_cloud.colors = o3d.utility.Vector3dVector(colors)

        elif scalarfield == "id":
            z_min = np.min(self.scalarfields["id"])
            z_max = np.max(self.scalarfields["id"])
            z_normalized = (self.scalarfields["id"] - z_min) / (z_max - z_min)
            colors = cm.viridis(z_normalized)[:, :3]
            point_cloud.colors = o3d.utility.Vector3dVector(colors)

        elif scalarfield == "class_id":
            z_min = np.min(self.scalarfields["class_id"])
            z_max = np.max(self.scalarfields["class_id"])
            z_normalized = (self.scalarfields["class_id"] - z_min) / (
                z_max - z_min
            )
            colors = cm.viridis(z_normalized)[:, :3]
            point_cloud.colors = o3d.utility.Vector3dVector(colors)
        elif scalarfield == "intensity":
            z_min = np.min(self.intensity)
            z_max = np.max(self.intensity)
            z_normalized = (self.intensity - z_min) / (z_max - z_min)
            colors = cm.viridis(z_normalized)[:, :3]
            point_cloud.colors = o3d.utility.Vector3dVector(colors)
        vis = o3d.visualization.Visualizer()
        vis.create_window()

        vis.add_geometry(point_cloud)

        # Minimum point
        xyz_min = np.min(self.xyz - self.txyz, axis=0)
        # xyz_max = np.max(self.xyz - self.txyz, axis=0)

        # Create coordiante origin and axes
        grid = o3d.geometry.TriangleMesh.create_coordinate_frame(
            size=0.5, origin=xyz_min
        )

        # Oriented bounding box
        obb = point_cloud.get_axis_aligned_bounding_box()
        obb.color = [1, 0, 0]
        vis.add_geometry(obb)
        vis.add_geometry(grid)

        vis.run()
        vis.destroy_window()

    def compute_dem(
        self,
        xylimits: np.array = np.array([0, 0, 0, 0]),
        dxy: float = 0.02,
        vis: bool = False,
    ) -> None:
        """Computes the Digital Elevation Model for the input point cloud

        Args:
            xylimits (np.array, optional): The limits for the XY plane. Defaults to np.array([0, 0, 0, 0]).
            dxy (float, optional): The resolution of the grid. Defaults to 0.02.
            vis (bool, optional): Whether to visualize the DEM. Defaults to False.
        """  # noqa: E501

        # xylimits [x_min, x_max, y_min, y_max]

        # Adjust grid to ensure last point falls within range
        x_bins = np.arange(xylimits[0], xylimits[1] + dxy + 1e-9, dxy)
        y_bins = np.arange(xylimits[2], xylimits[3] + dxy + 1e-9, dxy)

        # Bin Indices of the Points
        x_indices = np.digitize(self.xyz[:, 0], x_bins) - 1
        y_indices = np.digitize(self.xyz[:, 1], y_bins) - 1

        # Clip indices to ensure they are within valid range
        x_indices = np.clip(x_indices, 0, len(x_bins) - 2)
        y_indices = np.clip(y_indices, 0, len(y_bins) - 2)

        # Initialize array to track maximum height values
        Z_max = np.full((len(y_bins) - 1, len(x_bins) - 1), -np.inf)

        # Calculate the maximum height value for each grid cell
        np.maximum.at(Z_max, (y_indices, x_indices), self.xyz[:, 2])

        # Set undefined values to zero
        Z_max[Z_max == -np.inf] = np.nan

        if vis:

            plt.figure()

            plt.get_current_fig_manager().window.showMaximized()

            plt.imshow(
                Z_max,
                extent=(
                    np.min(x_bins),
                    np.max(x_bins),
                    np.min(y_bins),
                    np.max(y_bins),
                ),
                origin="lower",
                cmap="jet",
            )
            # Add a colorbar to the plot
            cd = plt.colorbar()
            cd.set_label("Ground height [m]", fontsize=12)
            plt.xlabel("X-Axis [m]", fontsize=12)
            plt.ylabel("Y-Axis [m]", fontsize=12)
            plt.title("Digital Elevation Model (DEM)", fontsize=15)
            plt.axis("equal")
            plt.xlim([np.min(x_bins), np.max(x_bins)])
            plt.ylim([np.min(y_bins), np.max(y_bins)])
            plt.show()

    # region show methods

    def show(
        self,
        color: Color = Color.Custom,
        cmap: str = "viridis",
        rgb: str = "",
        point_size: float = 3.0,
        parallel_projection: bool = True,
        non_blocking: bool = False,
    ) -> None:
        """Show the point cloud.

        Args:
            color               (Color, optional): Color mode for visualization. Defaults to Color.Custom.
            cmap                (str,   optional): Colormap to use. Defaults to "viridis".
            rgb                 (str,   optional): Color for custom coloring. Defaults to "".
                                                   Only required if color is Color.Custom.
            point_size          (float, optional): Size of the points. Defaults to 3.0.
            parallel_projection (bool,  optional): Enable parallel projection. Defaults to True.
            non_blocking        (bool,  optional): Run in non-blocking mode (window stays open). Defaults to False.
        """  # noqa: E501

        # Initialize PyVista plotter for interactive visualization
        pl = pv.Plotter()

        Visualization._show_addVis(
            self, pl, color, cmap, rgb, None, False, point_size
        )

        # Configure visual appearance
        pl.background_color = "#FFFFFF"
        pl.enable_eye_dome_lighting()  # Enhance depth perception

        # Enable parallel projection if requested (removes perspective)
        if parallel_projection:
            pl.enable_parallel_projection()

        # Display both point clouds in interactive window
        if non_blocking:
            pl.show(
                interactive_update=True, auto_close=False, full_screen=True
            )
        else:
            pl.show(full_screen=True)

        return

    def show_pair(
        self,
        pcIn: PointCloud,
        color1: str = "#ff0000",
        color2: str = "#00ff00",
        point_size: float = 3.0,
        parallel_projection: bool = True,
        non_blocking: bool = False,
    ) -> None:
        """Show two point clouds for comparison.

        Args:
            pcIn                (PointCloud):     Second point cloud to display.
            color1              (str,  optional): Color for the first point cloud. Defaults to "#ff0000".
            color2              (str,  optional): Color for the second point cloud. Defaults to "#00ff00".
            point_size          (float, optional): Size of the points. Defaults to 3.0.
            parallel_projection (bool, optional): Enable parallel projection. Defaults to True.
            non_blocking        (bool, optional): Run in non-blocking mode (window stays open). Defaults to False.
        """  # noqa: E501

        # Initialize PyVista plotter for side-by-side comparison
        pl = pv.Plotter()

        # Add first point cloud with specified color
        Visualization._show_addVis(
            self,
            pl,
            Visualization.Color.Custom,
            None,
            color1,
            None,
            False,
            point_size,
        )

        # Add second point cloud with contrasting color
        Visualization._show_addVis(
            pcIn,
            pl,
            Visualization.Color.Custom,
            None,
            color2,
            None,
            False,
            point_size,
        )

        if parallel_projection:
            pl.enable_parallel_projection()

        # Display both point clouds in interactive window
        if non_blocking:
            pl.show(
                interactive_update=True, auto_close=False, full_screen=True
            )
        else:
            pl.show(full_screen=True)

        return

    def show_compare(
        self,
        pcIn: PointCloud,
        color1: Color = Color.Height,
        color2: Color = Color.Height,
        cmap1: str = "viridis",
        cmap2: str = "viridis",
        rgb1: str = "#ff0000",
        rgb2: str = "#00ff00",
        point_size: float = 3.0,
        parallel_projection: bool = True,
        non_blocking: bool = False,
    ) -> None:
        """Show two point clouds side-by-side for comparison.

        Args:
            pcIn                (PointCloud):      Second point cloud to display.
            color1              (Color, optional): Color mode for first point cloud. Defaults to Color.Height.
            color2              (Color, optional): Color mode for second point cloud. Defaults to Color.Height.
            cmap1               (str,   optional): Colormap for first point cloud. Defaults to "viridis".
            cmap2               (str,   optional): Colormap for second point cloud. Defaults to "viridis".
            rgb1                (str,   optional): Custom color for first point cloud. Defaults to "#ff0000".
            rgb2                (str,   optional): Custom color for second point cloud. Defaults to "#00ff00".
            point_size          (float, optional): Size of the points. Defaults to 3.0.
            parallel_projection (bool,  optional): Enable parallel projection. Defaults to True.
            non_blocking        (bool,  optional): Run in non-blocking mode (window stays open). Defaults to False.
        """  # noqa: E501

        # Create side-by-side plotter
        pl = pv.Plotter(shape=(1, 2))

        # --- Left subplot: First point cloud (self) ---
        pl.subplot(0, 0)

        Visualization._show_addVis(
            self, pl, color1, cmap1, rgb1, None, False, point_size
        )

        # --- Right subplot: Second point cloud (pcIn) ---
        pl.subplot(0, 1)

        Visualization._show_addVis(
            pcIn, pl, color2, cmap2, rgb2, None, False, point_size
        )

        if parallel_projection:
            pl.enable_parallel_projection()

        # Link the cameras for synchronized navigation
        pl.link_views()

        # Display both point clouds in interactive window
        if non_blocking:
            pl.show(
                interactive_update=True, auto_close=False, full_screen=True
            )
        else:
            pl.show(full_screen=True)

        return

    def show_scalar_field(
        self,
        scalar_field: str,
        cmap: str = "viridis",
        point_size: float = 3.0,
        is_discrete: bool = False,
        parallel_projection: bool = True,
        non_blocking: bool = False,
    ) -> None:
        """Show point cloud colored by a scalar field.

        Args:
            scalar_field        (str):            The scalar field to visualize.
            cmap                (str,  optional): Colormap to use. Defaults to "viridis".
            point_size          (float, optional): Size of the points. Defaults to 3.0.
            is_discrete         (bool, optional): Whether the scalar field is discrete/categorical. Defaults to False.
            parallel_projection (bool, optional): Enable parallel projection. Defaults to True.
            non_blocking        (bool, optional): Run in non-blocking mode (window stays open). Defaults to False.
        """  # noqa: E501

        # Initialize PyVista plotter
        pl = pv.Plotter()

        # Convert point cloud to PyVista PolyData format
        Visualization._show_addVis(
            self,
            pl,
            Visualization.Color.ScalarField,
            cmap,
            None,
            scalar_field,
            is_discrete,
            point_size,
        )

        # Configure visual appearance
        pl.background_color = "#FFFFFF"
        pl.enable_eye_dome_lighting()  # Enhance depth perception

        if parallel_projection:
            pl.enable_parallel_projection()

        # Display both point clouds in interactive window
        if non_blocking:
            pl.show(
                interactive_update=True, auto_close=False, full_screen=True
            )
        else:
            pl.show(full_screen=True)

        return

    @staticmethod
    def _show_addVis(
        pc: PointCloud,
        pl: pv.Plotter,
        color: Color,
        cmap: str,
        rgb: str,
        scalar_field: str,
        is_discrete: bool,
        point_size: float,
    ) -> None:
        """Add a point cloud to the plotter with specified visualization parameters.

        Args:
            pc           (PointCloud): The point cloud to visualize.
            pl           (pv.Plotter): The PyVista plotter instance.
            color        (Color):      The color mode for visualization.
            cmap         (str):        The colormap to use.
            rgb          (str):        The RGB color value.
            scalar_field (str):        The scalar field to visualize.
            point_size   (float):      The size of the points.
        """  # noqa: E501

        # Convert point cloud coordinates to PyVista PolyData format
        cloud = pv.PolyData(pc.xyz)

        # Determine scalar field based on selected color mode
        match color:
            case Visualization.Color.Intensity:
                scalar = pc.intensity

            case Visualization.Color.Height:
                scalar = pc.xyz[:, 2]

            case Visualization.Color.Custom:
                scalar = None

                # Use default red color if no custom color specified
                if rgb == "":
                    rgb = "#ff0000"

            case Visualization.Color.ScalarField:
                scalar = pc.scalarfields[scalar_field]

        # Add point cloud mesh with color-specific rendering settings
        if color == Visualization.Color.Custom:
            # Custom color mode: use solid RGB color
            pl.add_mesh(
                cloud,
                style="points",
                render_points_as_spheres=False,
                emissive=False,
                color=rgb,
                point_size=point_size,
            )

        elif is_discrete:

            unique_values = np.unique(scalar)
            n_categories = len(unique_values)

            pl.add_mesh(
                cloud,
                style="points",
                render_points_as_spheres=False,
                emissive=False,
                scalars=scalar,
                cmap=cmap,
                point_size=point_size,
                categories=n_categories,  # Enable categorical coloring
            )
        else:

            pl.add_mesh(
                cloud,
                style="points",
                render_points_as_spheres=False,
                emissive=False,
                scalars=scalar,
                cmap=cmap,
                point_size=point_size,
            )

    # endregion pcshow methods
