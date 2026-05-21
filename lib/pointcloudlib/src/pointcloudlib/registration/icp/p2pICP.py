import random
import time

import numpy as np
from colorama import Fore, Style
from pointcloudlib.registration.icp.p2pICP_config import p2pICPconfig
from sklearn.neighbors import NearestNeighbors
from pointcloudlib import PointCloud
from pointcloudlib.utils import RotMat


class SymPlane2PlaneICP:

    pc1: PointCloud
    pc2: PointCloud

    def __init__(self, pc1, pc2, x=np.zeros(6), max_iter=50, dmax=0.06):
        self.pc1 = pc1  # point cloud 1
        self.pc2 = pc2  # point cloud 2
        self.pc_i = None  # Matches 1 & 2
        self.xyzm1 = None  # point matches 1
        self.xyzm2 = None  # point matches 2
        self.x = x  # Parameter vector of the current iteration
        self.dx = np.array(
            [0, 0, 0, 0, 0, 0]
        )  # Change of the parameter vector on each iteration
        self.max_iter = max_iter  # Maximum number of iterations
        self.dmax = dmax  # Maximum distance of matching points
        self.idxpc1, self.idxpc2 = np.arange(0, len(pc1.xyz)), np.arange(
            0, len(pc2.xyz)
        )  # Point indices of the point clouds
        self.idxmatches12 = None  # Indices of the point cloud matches
        self.iterations = 0  # Iteration counter

    def runICP(self, config: p2pICPconfig, symmetric: bool = True):
        """Run the ICP."""

        # Get transformation from initial guess parameters
        r, p, y, t1, t2, t3 = self.x
        R = RotMat.from_euler(r, p, y)
        t = np.array([t1 / 2, t2 / 2, t3 / 2])
        Hl = self.create_homogeneous_matrix(R.T, -t)
        Hr = self.create_homogeneous_matrix(R, t)
        
        # Accumulator for the full transformation of pc2 (if asymmetric)
        H_total_asym = np.eye(4)

        # Print info
        print(
            " ______________________________________________________________________________"
        )
        print(
            (f"| {Style.BRIGHT}{Fore.GREEN}Running ICP (Symmetric={symmetric}){Style.RESET_ALL}")
        )

        for iter in range(config.max_iterations):
            iter_start_time = time.time()

            # Compute point-to-point matches based on distance
            self.matching(config)

            # Estimate transformation with matched points
            self.estimateTrafo()

            # Apply transformation to point clouds and point matches
            if symmetric:
                self.transform_pointcloud(dx=self.dx, left_right="left")
                self.transform_pointcloud(dx=self.dx, left_right="right")

                self.xyzm1 = self.transform_points(X=self.xyzm1, left_right="left")
                self.xyzm2 = self.transform_points(
                    X=self.xyzm2, left_right="right"
                )
            else:
                # Asymmetric: Transform only the right point cloud with the full relative transformation
                R_dx = RotMat.from_euler(self.dx[0], self.dx[1], self.dx[2])
                t_half = self.dx[3:] / 2
                dHl_step = self.create_homogeneous_matrix(R_dx.T, -t_half)
                dHr_step = self.create_homogeneous_matrix(R_dx, t_half)
                
                # full relative transformation: H_rel = Hl_step^-1 * Hr_step
                dH_rel = np.linalg.inv(dHl_step) @ dHr_step
                
                R_rel = dH_rel[:3, :3]
                t_rel = dH_rel[:3, 3]
                
                # Update pointcloud right (pc2) explicitly with the combined matrix step
                self.pc2.xyz = (R_rel @ self.pc2.xyz.T + t_rel[:, np.newaxis]).T
                self.pc2.bbox = self.pc2._get_bounding_box()
                self.pc2.txyz = self.pc2._get_center()
                
                # Update matches for right pointcloud
                self.xyzm2 = (R_rel @ self.xyzm2.T + t_rel[:, np.newaxis]).T

            # Update transformation matrices
            R = RotMat.from_euler(self.dx[0], self.dx[1], self.dx[2])
            t = self.dx[3:] / 2
            dHl = self.create_homogeneous_matrix(R.T, -t)
            dHr = self.create_homogeneous_matrix(R, t)
            Hl = dHl @ Hl
            Hr = dHr @ Hr
            
            if not symmetric:
                H_total_asym = dH_rel @ H_total_asym

            # Update iteration counter
            self.iterations += 1
            iter_end_time = time.time()
            elapsed_time = iter_end_time - iter_start_time
            n_matches = self.xyzm1.shape[0] if self.xyzm1 is not None else 0

            # Terminal output of the current iteration
            formatted_rot = ", ".join([f"{value:>8.5f}" for value in self.dx[:3]])
            formatted_trans = ", ".join([f"{value:>8.5f}" for value in self.dx[3:]])
            print(
                f"| {Style.BRIGHT}{Fore.WHITE}Iteration {self.iterations:02d}{Style.RESET_ALL} "
                f"| {Fore.CYAN}matches:{Style.RESET_ALL} {n_matches:<6} "
                f"| {Fore.YELLOW}time:{Style.RESET_ALL} {elapsed_time:>5.2f}s "
                f"| {Fore.MAGENTA}rot:{Style.RESET_ALL} [{formatted_rot}] "
                f"| {Fore.MAGENTA}trans:{Style.RESET_ALL} [{formatted_trans}]"
            )

            # Check if maximum of the parameter change is below treshold
            if max(abs(self.dx)) <= 10e-4:

                # Get final transformation
                if symmetric:
                    self.x = self.extract_parameters(Hr)
                else:
                    # In asymmetric mode, we return the total relative transformation
                    # Rotation is stored as euler angels, translation is full.
                    self.x[:3] = RotMat.to_euler(H_total_asym[:3, :3])
                    self.x[3:] = H_total_asym[:3, 3]

                print(
                    (
                        f"| {Style.BRIGHT}{Fore.GREEN}ICP converged at iteration {str(iter + 1)}{Style.RESET_ALL}"
                    )
                )
                print(
                    "Estimated transformation: rx [rad], ry [rad], rz [rad], tx [m], ty [m], tz [m] \n",
                    self.x,
                )
                print(
                    " ______________________________________________________________________________"
                )

                return self.x, self.pc1, self.pc2

        # If not converged
        print(
            (
                f"| {Style.BRIGHT}{Fore.RED}{'ICP did not converge after iteration ' + str(self.max_iter)}{Style.RESET_ALL}"
            )
        )
        print(
            "|_______________________________________________________________"
        )

        self.x[:] = np.nan * np.ones(6)
        return self.x, False, self.pc1, self.pc2

    def matching(self, config: p2pICPconfig):
        """Find matches between the two point clouds."""

        # Voxeldownsampling of the first point cloud
        pc1_downsampled, idv1 = self.pc1.subsample(
            method="voxelRandom", voxel_size=config.voxel_size
        )

        # Indices of the voxel point of the dataset
        idxtmpv = self.idxpc1[idv1]

        # Compute nearest neighbor distances to voxelized point cloud
        nbrs = NearestNeighbors(n_neighbors=1, algorithm="auto").fit(
            self.pc2.xyz
        )
        dNN, idxNN = nbrs.kneighbors(pc1_downsampled.xyz)

        # Filter matches by distances threshold
        valid_mask = dNN[:, 0] < config.max_dist

        # Store indices of the matches
        self.idxmatches12 = np.c_[
            idxtmpv[valid_mask], self.idxpc2[idxNN[valid_mask, 0]]
        ]

        # Store point matches idx
        self.mx1 = pc1_downsampled.xyz[valid_mask]
        self.mx2 = self.pc2.xyz[idxNN[valid_mask, 0]]
        self.pc_i = np.hstack((self.mx1, self.mx2))

        # Compute normals and roughness for pc1
        n1, std1, idx = self.normals(
            self.mx1,
            self.pc1.xyz,
            config.normals_radius,
            config.normals_minpoints,
        )  # n: [nx, ny, nz, roughness]
        self.mx1, self.mx2 = self.mx1[idx], self.mx2[idx]
        self.idxmatches12 = self.idxmatches12[idx]

        # Filter by roughness
        if config.roughness_filter_use:
            idx = std1 <= config.max_roughness
            self.mx1, self.mx2, n1 = self.mx1[idx], self.mx2[idx], n1[idx]
            self.idxmatches12 = self.idxmatches12[idx]

        # Compute normals and roughness for pc2
        n2, std2, idx = self.normals(
            self.mx2,
            self.pc2.xyz,
            config.normals_radius,
            config.normals_minpoints,
        )  # n: [nx, ny, nz, roughness]
        self.mx1, self.mx2, n1 = self.mx1[idx], self.mx2[idx], n1[idx]
        self.idxmatches12 = self.idxmatches12[idx]

        # Filter by roughness value
        if config.roughness_filter_use:
            idx = std2 <= config.max_roughness
            self.mx1, self.mx2, n1, n2 = (
                self.mx1[idx],
                self.mx2[idx],
                n1[idx],
                n2[idx],
            )
            self.idxmatches12 = self.idxmatches12[idx]

        # Compute sum of scalar product
        sp = np.sum(n1 * n2, axis=1)

        # Filter by angle between normals
        if config.normal_angle_use:
            alpha_max = np.radians(config.normal_angle_max)
            th = np.cos(alpha_max)
            idx = np.abs(sp) >= th
            self.mx1, self.mx2, n1, n2, sp = (
                self.mx1[idx],
                self.mx2[idx],
                n1[idx],
                n2[idx],
                sp[idx],
            )
            self.idxmatches12 = self.idxmatches12[idx]

        # Compute mean normal and point-to-plane distance
        idx = sp < 0
        n2[idx] = -n2[idx]
        n = 0.5 * (n1 + n2)
        dx = self.mx2 - self.mx1
        p2p_d = np.sum(n * dx, axis=1)

        # Filter by point-to-plane MAD
        if config.mad_use:
            s_mad = 1.4826 * np.median(np.abs(p2p_d - np.median(p2p_d)))
            idx = np.abs(p2p_d - np.median(p2p_d)) <= 3 * s_mad
            self.mx1, self.mx2, n = self.mx1[idx], self.mx2[idx], n[idx]
            self.idxmatches12 = self.idxmatches12[idx]

        # Update filtered matches
        self.pc_i = np.hstack((self.mx1, self.mx2, n))

        # Matching points
        self.xyzm1 = self.mx1
        self.xyzm2 = self.mx2

    def estimateTrafo(self):
        """Estimate the rigid body transformation from matched points."""
        x1 = self.pc_i[:, :3]
        x2 = self.pc_i[:, 3:6]
        normals = self.pc_i[:, 6:]

        # estimate rigid body transformaton
        A = np.zeros([x1.shape[0], 6])
        A[:, 0] = (
            -normals[:, 1] * x2[:, 2]
            + normals[:, 2] * x2[:, 1]
            - normals[:, 1] * x1[:, 2]
            + normals[:, 2] * x1[:, 1]
        )
        A[:, 1] = (
            normals[:, 0] * x2[:, 2]
            - normals[:, 2] * x2[:, 0]
            + normals[:, 0] * x1[:, 2]
            - normals[:, 2] * x1[:, 0]
        )
        A[:, 2] = (
            -normals[:, 0] * x2[:, 1]
            + normals[:, 1] * x2[:, 0]
            - normals[:, 0] * x1[:, 1]
            + normals[:, 1] * x1[:, 0]
        )
        A[:, 3:] = normals
        l = (
            normals[:, 0] * (x1[:, 0] - x2[:, 0])
            + normals[:, 1] * (x1[:, 1] - x2[:, 1])
            + normals[:, 2] * (x1[:, 2] - x2[:, 2])
        )

        # Huber weighting with
        sigma = 1.4826 * np.median(np.abs(np.abs(l) - np.median(np.abs(l))))

        v = l / sigma

        # recude by median
        v = np.abs(v) - np.median(np.abs(v))

        idx_0 = v == 0
        v[idx_0] = 1
        w = self.Psi_Huber(v) / v
        A = A * w[:, np.newaxis]
        l = l * w

        # Compute updates on the parameter
        dx = np.linalg.lstsq(A, l, rcond=None)
        self.dx = dx[0]

        # Compute cofactor matrix
        Qdxdx = np.linalg.inv(A.T @ A)

        # Compute correlation matrix
        self.compute_correlation_matrix(Qdxdx, print_matrix=False)

    def filter_invalid_points(self, pc):
        valid_mask = np.all(np.isfinite(pc), axis=1)
        return pc[valid_mask]

    def extract_parameters(self, Hr):
        x = np.zeros(6)
        x[:3] = RotMat.to_euler(Hr[:3, :3])
        x[3:] = 2 * Hr[:3, 3]
        return x

    def create_homogeneous_matrix(self, R, t):

        if R.shape != (3, 3):
            raise ValueError("Rotation matrix R must be 3x3.")

        if t.shape != (3,) and t.shape != (3, 1):
            raise ValueError("Translation vector t must be a 3x1 vector.")

        t = t.reshape(3, 1)

        H = np.eye(4)
        H[:3, :3] = R
        H[:3, 3] = t.flatten()

        return H

    def transform_points(self, X, left_right):
        """Splits and applies the ICP transformation parameters to two point clouds.

        Args:
            self.dx
            self.pc1 // self.pc2
            left_right : either left or right scanner

        Returns:
            x : newly transformed point
        """

        r, p, y, t1, t2, t3 = self.dx

        R = RotMat.from_euler(r, p, y)
        translation = np.array([t1 / 2, t2 / 2, t3 / 2])

        if left_right == "right":
            x = R @ X.T + translation[:, np.newaxis]
        else:
            x = R.T @ X.T - translation[:, np.newaxis]

        return x

    def transform_pointcloud(self, dx, left_right):
        """Splits and applies the ICP transformation parameters to two point clouds.

        Args:
            self.dx
            self.pc1 // self.pc2
            left_right : either left or right scanner

        Returns:
            x : newly transformed point
        """

        r, p, y, t1, t2, t3 = dx

        R = RotMat.from_euler(r, p, y)
        translation = np.array([t1 / 2, t2 / 2, t3 / 2])

        if left_right == "P2":
            self.pc2.xyz = (R @ self.pc2.xyz.T + translation[:, np.newaxis]).T
            self.pc2.bbox = self.pc2._get_bounding_box()
            self.pc2.txyz = self.pc2._get_center()
        else:
            self.pc1.xyz = (
                R.T @ self.pc1.xyz.T - translation[:, np.newaxis]
            ).T
            self.pc1.bbox = self.pc1._get_bounding_box()
            self.pc1.txyz = self.pc1._get_center()

    def Psi_Huber(self, v, k=2):
        idx = np.abs(v) > k
        v[idx] = np.sign(v[idx]) * k
        return v

    def normals(self, x, pc, r, minPts, maxPts: int = 1000):
        nbrs = NearestNeighbors(radius=r, algorithm="auto").fit(pc)
        n = []
        std = []

        discarded_indices = []
        for idx, point in enumerate(x):
            _, indices = nbrs.radius_neighbors([point])
            if len(indices[0]) >= minPts:
                neighbors = pc[indices[0]]

                # random subsampling of the neighbors if the number is too large
                if len(neighbors) > maxPts:  # TODO: read from config file !
                    idx_r = random.sample(range(0, len(neighbors) - 1), maxPts)
                    neighbors = neighbors[idx_r]

                plane_normal, std_dev = self.plane_fitting(neighbors)
                n.append(plane_normal)
                std.append(std_dev)
            else:
                discarded_indices.append(idx)
        kept_indices = [i for i in range(len(x)) if i not in discarded_indices]
        return np.array(n), np.array(std), kept_indices

    def plane_fitting(self, points):
        # compute normal
        centroid = np.mean(points, axis=0)
        centered_points = points - centroid
        _, _, vh = np.linalg.svd(centered_points)
        plane_normal = vh[-1, :]
        # compute point2plane distances
        d = -np.dot(plane_normal, centroid)
        distances = np.abs(np.dot(points, plane_normal) + d) / np.linalg.norm(
            plane_normal
        )
        # compute rougness
        variance_factor = np.sum(distances**2) / (points.shape[0] - 3)
        std_dev = np.sqrt(variance_factor)
        return plane_normal, std_dev  # [nx,ny,nz,roughness]

    @staticmethod
    def compute_correlation_matrix(
        Q, print_matrix: bool = False
    ) -> np.ndarray:
        std_devs = np.sqrt(np.diag(Q))
        corr_matrix = Q / np.outer(std_devs, std_devs)

        # Print matrix (if specified)
        if print_matrix:
            np.set_printoptions(precision=4, suppress=True)
            print(corr_matrix)
            np.set_printoptions()

        return corr_matrix
