from typing import Union

import matplotlib.pyplot as plt
import numpy as np
import scipy.sparse as sp
from colorama import Fore, Style
from sklearn.decomposition import PCA

from pointcloudlib import PointCloud
from pointcloudlib.least_squares_adjustments.estimator import Estimator


class PlaneAdjustment(Estimator):
    def __init__(
        self,
        pc: Union[PointCloud, None] = None,
        initialParams: Union[np.ndarray, None] = None,
        params: Union[np.ndarray, None] = None,
        v: Union[np.ndarray, None] = None,
        w: Union[np.ndarray, None] = None,
        d_p2p: Union[np.ndarray, None] = None,
        it_counter: Union[int, None] = 0,
        maxIter: Union[int, None] = 50,
        epsilon: Union[float, None] = 1e-08,
    ):
        super().__init__(
            pc, initialParams, params, v, w, it_counter, maxIter, epsilon
        )  # Point cloud object                  # Residuals ("Verbesserungen")
        self.d_p2p = d_p2p  # Point-to-plane distancess
        self.d = None
        self.normal = None

    def computeInitialGuess(self):
        """
        abstract method for computing initial guess
        """
        XYZ = self.pc.xyz
        pca = PCA(n_components=3)
        pca.fit(XYZ)
        n0 = pca.components_[-1]
        d0 = np.mean(np.linalg.norm(XYZ, axis=1))
        self.initialParams = n0 / d0
        return

    def discrepancies(self, l0, x0):
        p = self.pc.xyz.shape[0]
        X0 = l0[0:p]
        Y0 = l0[p : 2 * p]
        Z0 = l0[2 * p :]

        nx, ny, nz = x0

        return nx * X0 + ny * Y0 + nz * Z0 - 1

    def designmatrix(self, l0, x0):
        p = self.pc.xyz.shape[0]
        X0 = l0[0:p]
        Y0 = l0[p : 2 * p]
        Z0 = l0[2 * p :]

        p = self.pc.xyz.shape[0]
        u = 3
        A = np.zeros((p, u))
        A[:, 0] = X0
        A[:, 1] = Y0
        A[:, 2] = Z0

        return A

    def conditionmatrix(self, l0, x0):
        p = self.pc.xyz.shape[0]
        # Set current normal vector
        nx, ny, nz = x0

        # Set up conditional matrix B (Jacobians w.r.t. measurements)
        Bx = sp.diags(np.ones(p) * nx)
        By = sp.diags(np.ones(p) * ny)
        Bz = sp.diags(np.ones(p) * nz)
        B = sp.hstack([Bx, By, Bz], format="csr")  # size p x m

        return B

    def computeP2P(self):
        # Compute point-to-plane distances
        d_est = 1 / np.linalg.norm(self.params)
        n_est = self.params * d_est
        nx, ny, nz = n_est
        denominator = np.sqrt(nx**2 + ny**2 + nz**2)

        # Set class variables
        self.d_p2p = (
            nx * self.pc.xyz[:, 0]
            + ny * self.pc.xyz[:, 1]
            + nz * self.pc.xyz[:, 2]
            - d_est
        ) / denominator
        self.normal = n_est
        self.d = d_est

    def print_results(self) -> None:

        print(
            (
                " ____________________________________________________________________________\n"
                "| \n"
                f"| {Style.BRIGHT}{Fore.MAGENTA}{'Least-squares Results'}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- Number of iterations:        '+ str(self.it_counter)}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- x:                           ' + str(self.normal)}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- v*v^T [mm]:                  '}{np.dot(self.v, self.v)*1000:.4f}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- mean (p2p) [mm]:             '}{np.mean(self.d_p2p) * 1000:.4f}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- std (p2p) [mm]:              '}{np.std(self.d_p2p) * 1000:.4f}{Style.RESET_ALL}\n"
                f"|___________________________________________________________________________\n"
            )
        )

    def visualize_results(self) -> None:

        # Plot point cloud with distance colors
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        sc = ax.scatter(
            self.pc.xyz[:, 0],
            self.pc.xyz[:, 1],
            self.pc.xyz[:, 2],
            c=self.d_p2p * 1000,
            cmap="viridis",
        )
        plt.colorbar(sc, label="Distances [mm]")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title("Point cloud colored by point-to-plane distance")
        plt.grid(True)
        plt.axis("equal")
        plt.show()

        # Plot histogram of the point-to-plane distances
        plt.figure()
        plt.hist(self.d_p2p * 1000, bins=100)
        plt.xlabel("Distances in [mm]")
        plt.ylabel("Counts")
        plt.grid()
        plt.title("Histogram of point-to-plane distances")
        plt.show()

    def run(self):
        super().run()
        self.computeP2P()

    # def run(self):

    #     # Transform the points to local coordinate frame
    #     XYZ = self.pc.xyz - np.min(self.pc.xyz, axis=0)

    #     # Determine dimensions for least-squares
    #     p = XYZ.shape[0] # number of points (= c: number of condition equations)
    #     m = p * 3        # number of measurements
    #     u = 3            # number of parameters
    #     r = p-u          # redundancy

    #     # Initial guess parameter with PCA
    #     pca = PCA(n_components=3)
    #     pca.fit(XYZ)
    #     n0 = pca.components_[-1]
    #     d0 = np.mean(np.linalg.norm(XYZ, axis=1))
    #     x0 = n0 / d0

    #     # Measurement vector and stochastic model
    #     L = np.concatenate((XYZ[:,0], XYZ[:,1], XYZ[:,2]))
    #     L0 = L.copy()

    #     # Covariance matrix (identity)
    #     S_diag = np.ones(m)
    #     S = sp.diags(S_diag)
    #     s0 = 1
    #     Q = S * (1 / s0**2)

    #     # Main loop
    #     isconverged = False

    #     print(( " ____________________________________________________________________________"))
    #     print(f"| {Style.BRIGHT}{Fore.MAGENTA}Starting Least-Squares Plane Optimization {Style.RESET_ALL}")

    #     while isconverged == False:

    #         # Extract the current measurements
    #         X0 = L0[:p]
    #         Y0 = L0[p:2*p]
    #         Z0 = L0[2*p:]

    #         # Set current normal vector
    #         nx, ny, nz = x0

    #         # Set up conditional matrix B (Jacobians w.r.t. measurements)
    #         Bx = sp.diags(np.ones(p) * nx)
    #         By = sp.diags(np.ones(p) * ny)
    #         Bz = sp.diags(np.ones(p) * nz)
    #         B = sp.hstack([Bx, By, Bz], format='csr')  # size p x m

    #         # Set up configuration matrix A (Jacobians w.r.t. parameter)
    #         A = np.zeros((p, u))
    #         A[:,0] = X0
    #         A[:,1] = Y0
    #         A[:,2] = Z0

    #         # Compute discrepancy vector W
    #         W = nx * X0 + ny * Y0 + nz * Z0 - 1
    #         W = -(W + B @ (L - L0))
    #         M = B @ Q @ B.T  # p x p
    #         M_csc = M.tocsc()

    #         # Compute N and U
    #         N = A.T @ spla.spsolve(M_csc, A)
    #         U = A.T @ spla.spsolve(M_csc, W)

    #         # Solve to estimate parameter vector x
    #         x = la.solve(N, U)

    #         # Compute residuals
    #         self.v = Q @ B.T @ spla.spsolve(M_csc, W - A @ x)

    #         # Determine parameter vector and observations
    #         x_est = x + x0
    #         L_corr = L + self.v

    #         # Check for convergence or max iteration
    #         if np.max(np.abs(x)) < 1e-8 or self.it_counter > 50:
    #             isconverged = True
    #             print(f"| {Style.BRIGHT}{Fore.GREEN}Converged! {Style.RESET_ALL}")
    #         else:
    #             # Update parameter vector and observations
    #             x0 = x_est
    #             L0 = L_corr

    #             # Print some useful information about the current iteration
    #             print(f"| {Style.BRIGHT}{Fore.WHITE}Iteration: {self.it_counter:01}, v_squared: {np.dot(self.v, self.v):.4f}, dx: [{x[0]:4f},{x[1]:4f},{x[2]:4f}]{Style.RESET_ALL}")
    #             self.it_counter += 1

    #     # end while main
    #     print(( "|____________________________________________________________________________"))

    #     # Compute point-to-plane distances
    #     d_est = 1 / np.linalg.norm(x_est)
    #     n_est = x_est * d_est
    #     nx, ny, nz = n_est
    #     denominator = np.sqrt(nx**2 + ny**2 + nz**2)

    #     # Set class variables
    #     self.d_p2p = (nx*XYZ[:, 0] + ny*XYZ[:, 1] + nz*XYZ[:, 2] - d_est) / denominator
    #     self.normal = n_est
    #     self.d = d_est
