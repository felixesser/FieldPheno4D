import open3d as o3d
from pointcloudlib import PointCloud
import numpy as np
from pointcloudlib.utils import VerboseLevel
from colorama import Fore, Style


class ICP:
    """Iterative Closest Point (ICP) registration methods.

    Non-static methods are attached to the PointCloud class (see __init__.py).
    """  # noqa: E501

    def point_to_point_icp(
        self,
        target_pc: PointCloud,
        max_corr_dist: float = 0.05,
        max_iterations: int = 30,
        relative_fitness: float = 1e-6,
        relative_rmse: float = 1e-6,
        init_T: np.ndarray = None,
        verbose: int = VerboseLevel.SILENT,
    ) -> np.ndarray:
        """Point-to-point ICP registration between this point cloud (source)
        and the target point cloud.

        The method uses Open3D's implementation of the point-to-point ICP algorithm.

        Args:
            target_pc        (PointCloud):           Target point cloud.
            max_corr_dist    (float,      optional): Maximum correspondence distance.     Defaults to 0.05.
            max_iterations   (int,        optional): Maximum number of iterations.        Defaults to 30.
            relative_fitness (float,      optional): Relative fitness threshold.          Defaults to 1e-6.
            relative_rmse    (float,      optional): Relative RMSE threshold.             Defaults to 1e-6.
            init_T           (np.asarray, optional): Initial transformation matrix (4x4). Defaults to None.
            verbose          (int,        optional): Verbosity level.                     Defaults to VerboseLevel.SILENT.

        Returns:
            np.asarray: Transformation matrix (4x4).
        """  # noqa: E501

        # region output (console)

        if verbose > VerboseLevel.SILENT:
            print(
                f"{Style.BRIGHT}{Fore.MAGENTA}"
                "┏" + "━" * 40 + "┓\n"
                f"┃{'Point-to-point ICP':^40}┃\n"
                "┗" + "━" * 40 + "┛"
                f"{Style.RESET_ALL}\n"
            )

        # Debug output: Additional statistics
        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG] Input parameters:\n"
                f"  - Source points:                   {len(self.xyz):_}\n"
                f"  - Target points:                   {len(target_pc.xyz):_}\n"  # noqa: E501
                f"  - Maximum correspondence distance: {max_corr_dist}\n"
                f"  - Maximum iterations:              {max_iterations}\n"
                f"  - Relative fitness:                {relative_fitness}\n"
                f"  - Relative RMSE:                   {relative_rmse}"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        source = o3d.geometry.PointCloud()
        source.points = o3d.utility.Vector3dVector(self.xyz)

        target = o3d.geometry.PointCloud()
        target.points = o3d.utility.Vector3dVector(target_pc.xyz)

        ICPConvergenceCriteria = (
            o3d.pipelines.registration.ICPConvergenceCriteria(
                relative_fitness=relative_fitness,
                relative_rmse=relative_rmse,
                max_iteration=max_iterations,
            )
        )

        if init_T is None:
            init_T = np.eye(4)

        reg_p2p = o3d.pipelines.registration.registration_icp(
            source,
            target,
            max_corr_dist,
            init_T,
            o3d.pipelines.registration.TransformationEstimationPointToPoint(),
            ICPConvergenceCriteria,
        )

        # region output (console)

        if verbose >= VerboseLevel.INFO:
            corr_set_size = len(reg_p2p.correspondence_set)

            print(
                f"{Fore.WHITE}"
                f"[INFO] Registration result\n"
                f"  - Fitness:              {reg_p2p.fitness:.6f}\n"
                f"  - RMSE:                 {reg_p2p.inlier_rmse:.6f}\n"
                f"  - Correspondence count: {corr_set_size:_}"
                f"{Style.RESET_ALL}\n"
            )

        # Debug output: Additional statistics
        if verbose >= VerboseLevel.DEBUG:
            np.set_printoptions(precision=6, suppress=True)
            matrix_str = "\n".join(
                "    " + line
                for line in str(reg_p2p.transformation).split("\n")
            )
            print(
                f"{Fore.CYAN}[DEBUG] Transformation matrix:\n"
                f"{matrix_str}"
                f"{Style.RESET_ALL}\n"
            )
            np.set_printoptions()  # Reset to default

        # endregion output (console)

        return reg_p2p.transformation
