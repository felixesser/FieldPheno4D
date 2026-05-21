"""
Cleaning extensions for PointCloud class.
"""

import open3d as o3d
from colorama import Fore, Style
from pointcloudlib import PointCloud
from pointcloudlib.utils import VerboseLevel


class Cleaning:
    """Cleaning methods for point clouds
    (Denoising and Outlier Removal).

    Non-static methods are attached to the PointCloud class (see __init__.py).
    """  # noqa: E501

    def pcdenoise(
        self,
        nb_neighbors: int = 4,
        std_ratio: float = 1.0,
        verbose: int = VerboseLevel.SILENT,
    ) -> tuple[PointCloud, list]:
        """Remove noise from 3-D point cloud

        The method uses Open3D's statistical outlier removal to filter
        noisy points from the point cloud.

        Args:
            nb_neighbors (int,   optional): Number of neighbors to consider for each point. Defaults to 4.
            std_ratio    (float, optional): Standard deviation ratio for outlier detection. Defaults to 1.0.
            verbose      (int,   optional): Verbosity level (0=silent, 1=error, 2=warning, 3=info, 4=debug).
                                            Defaults to VerboseLevel.SILENT.

        Returns:
            tuple: A tuple containing:
                - PointCloud: The filtered point cloud with noise removed.
                - list: Indices of inlier points retained in the filtered point cloud.
                - list: Indices of outlier points removed from the original point cloud.
        """  # noqa: E501

        # region output (console)

        if verbose > VerboseLevel.SILENT:
            print(
                f"{Style.BRIGHT}{Fore.MAGENTA}"
                "┏" + "━" * 40 + "┓\n"
                f"┃{'Remove noise from 3-D point cloud':^40}┃\n"
                "┗" + "━" * 40 + "┛"
                f"{Style.RESET_ALL}\n"
            )

        # Debug output: Additional statistics
        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG] Input parameters:\n"
                f"  - nb_neighbors: {nb_neighbors}\n"
                f"  - std_ratio:    {std_ratio}\n"
                f"  - Input points: {len(self.xyz):_}"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        pc_in = o3d.geometry.PointCloud()
        pc_in.points = o3d.utility.Vector3dVector(self.xyz - self.txyz)

        _, inlier_indices = pc_in.remove_statistical_outlier(
            nb_neighbors=nb_neighbors, std_ratio=std_ratio
        )

        pc_out = self.select_by_index(inlier_indices)

        # region statistics

        # Calculate statistics
        pointsIn = len(self.xyz)
        pointsOut = len(pc_out.xyz)
        pointsRemoved = pointsIn - pointsOut
        removal_percentage = (
            (pointsRemoved / pointsIn * 100) if pointsIn > 0 else 0
        )

        # endregion statistics

        # region output (console)

        # Error output: Check if too many points were removed
        if verbose >= VerboseLevel.ERROR and removal_percentage > 50:
            print(
                f"{Fore.RED}[ERROR] More than 50% of points removed "
                f"({removal_percentage:.1f}%)! Check parameters."
                f"{Style.RESET_ALL}\n"
            )

        # Warning output: Check if significant points were removed
        if verbose >= VerboseLevel.WARNING and 20 < removal_percentage <= 50:
            print(
                f"{Fore.YELLOW}[WARNING] {removal_percentage:.1f}% of "
                f"points removed. Consider adjusting parameters."
                f"{Style.RESET_ALL}\n"
            )

        # Info output: General statistics
        if verbose >= VerboseLevel.INFO:
            print(
                f"{Fore.WHITE}"
                f"[INFO] Remove noise from 3-D point cloud\n"
                f"  - #points (in):    {pointsIn:_.0f}\n"
                f"  - #Removed points: {pointsRemoved:_.0f}\n"
                f"  - #points (out):   {pointsOut:_.0f}"
                f"{Style.RESET_ALL}\n"
            )

        # Debug output: Additional statistics
        if verbose >= VerboseLevel.DEBUG:
            outlier_indices = list(
                set(range(len(self.xyz))) - set(inlier_indices)
            )
            print(
                f"{Fore.CYAN}[DEBUG] Additional information:\n"
                f"  - Removal percentage:    {removal_percentage:.2f}%\n"
                f"  - Inlier indices count:  {len(inlier_indices):_}\n"
                f"  - Outlier indices count: {len(outlier_indices):_}"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        return pc_out, inlier_indices
