from typing import Union

import matplotlib.pyplot as plt
import numpy as np
import scipy.sparse as sp
import sympy as sym
from colorama import Fore, Style

from pointcloudlib.least_squares_adjustments.estimator import Estimator


def F_cylinder(x, y, z, r, w_x, w_y, x0, y0):
    f = (
        (
            (
                (y - y0) * sym.cos(w_x)
                + (x - x0) * sym.sin(w_x) * sym.sin(w_y)
                + z * sym.sin(w_x) * sym.cos(w_y)
            )
            / r
        )
        ** 2
        + (((x - x0) * sym.cos(w_y) - z * sym.sin(w_y)) / r) ** 2
        - 1
    )
    return f


# TO-DO
def compA_sym():
    X, Y, Z, R, WX, WY, XC, YC = sym.symbols("X Y Z R WX WY XC YC")
    F_Y = F_cylinder(
        X, Y, Z, R, WX, WY, XC, YC
    )  # Functional Relationship Symbolic
    A_sym = sym.Matrix([F_Y]).jacobian(
        sym.Matrix([R, WX, WY, XC, YC])
    )  # Designmatrix Symbolic

    return A_sym


def compB_sym():
    X, Y, Z, R, WX, WY, XC, YC = sym.symbols("X Y Z R WX WY XC YC")
    F_Y = F_cylinder(
        X, Y, Z, R, WX, WY, XC, YC
    )  # Functional Relationship Symbolic
    B_sym = sym.Matrix([F_Y]).jacobian(
        sym.Matrix([X, Y, Z])
    )  # Designmatrix Symbolic

    return B_sym


def fit2DCircleRANSAC(xy, thresh=0.05, numIters=1000):

    numInliers = np.zeros((numIters,))
    params = np.zeros((numIters, 3))
    indices_picked = np.zeros((numIters, 3), dtype=np.uint32)
    Inliers = []
    # maxInliers = 0
    n = len(xy)
    for iter in range(numIters):
        ids_pick = np.random.permutation(n)[0:3]
        xy_pick = xy[ids_pick, :]
        indices_picked[iter] = ids_pick
        l = -np.sum(xy_pick**2, axis=1)
        F = np.c_[np.ones((3,)), -xy_pick[:, 0], -xy_pick[:, 1]]

        ABC = np.linalg.solve(F, l)

        mean = ABC[1:] / 2
        radius = np.sqrt(np.sum(mean**2) - ABC[0])
        params[iter, :] = [mean[0], mean[1], radius]
        deltas = np.sqrt(np.sum((xy - mean) ** 2, axis=1)) - radius
        idx_inliers = np.where(deltas < thresh)[0]
        numInliers[iter] = len(idx_inliers)
        Inliers.append(idx_inliers)

    ids_best = np.argmax(numInliers)
    params_best = params[ids_best, :]

    center = params_best[0:2]
    radius = params_best[2]

    return center, radius


class CylinderAdjustment(Estimator):
    def __init__(
        self,
        pc: Union[pointcloud, None] = None,
        initialParams: Union[np.ndarray, None] = None,
        params: Union[np.ndarray, None] = None,
        v: Union[np.ndarray, None] = None,
        w: Union[np.ndarray, None] = None,
        it_counter: Union[int, None] = 0,
        maxIter: Union[int, None] = 50,
        epsilon: Union[float, None] = 1e-08,
        center: Union[np.ndarray, None] = None,
        radius: Union[float, None] = None,
        angles: Union[np.ndarray, None] = None,
    ):
        super().__init__(
            pc, initialParams, params, v, w, it_counter, maxIter, epsilon
        )
        self.center = center
        self.radius = radius
        self.angles = angles

    def computeInitialGuess(self):  # BUGGY
        _, pca = self.pc.PCA(transform_points=False)
        xyz_trafo = pca.transform(self.pc.xyz)
        axis = pca.components_[0, :]
        angle_y = np.arcsin(axis[0])
        angle_x = -np.arcsin(axis[1] / np.cos(angle_y))

        mean, radius = fit2DCircleRANSAC(
            xyz_trafo[:, 1:3], thresh=0.02, numIters=1000
        )
        meanPt_trafo = np.array([[0, mean[0], mean[1]]])
        meanPt = pca.inverse_transform(meanPt_trafo).flatten()

        s_intersect = -meanPt[2] / axis[2]
        meanPt_projected = meanPt + s_intersect * axis
        x0 = meanPt_projected[0]
        y0 = meanPt_projected[1]

        self.initialParams = np.array([radius, angle_x, angle_y, x0, y0])

        return

    def discrepancies(self, l0, x0):
        p = self.pc.xyz.shape[0]

        X0 = l0[0:p]
        Y0 = l0[p : 2 * p]
        Z0 = l0[2 * p :]

        r, w_x, w_y, xc, yc = x0

        f = (
            (
                (
                    (Y0 - yc) * np.cos(w_x)
                    + (X0 - xc) * np.sin(w_x) * np.sin(w_y)
                    + Z0 * np.sin(w_x) * np.cos(w_y)
                )
                / r
            )
            ** 2
            + (((X0 - xc) * np.cos(w_y) - Z0 * np.sin(w_y)) / r) ** 2
            - 1
        )
        return f

    def designmatrix(self, l0, x0):
        p = self.pc.xyz.shape[0]

        X0 = l0[0:p]
        Y0 = l0[p : 2 * p]
        Z0 = l0[2 * p :]

        r, w_x, w_y, xc, yc = x0
        # ### Symbolics Sympy ###
        X, Y, Z, R, WX, WY, XC, YC = sym.symbols("X Y Z R WX WY XC YC")

        A_sym = compA_sym()
        a = sym.lambdify((X, Y, Z, R, WX, WY, XC, YC), A_sym, "numpy")
        A_vals = [
            a(x, y, z, r, w_x, w_y, xc, yc) for x, y, z in zip(X0, Y0, Z0)
        ]
        A = np.concatenate(A_vals, axis=0)

        return A

    def conditionmatrix(self, l0, x0):
        p = self.pc.xyz.shape[0]

        X0 = l0[0:p]
        Y0 = l0[p : 2 * p]
        Z0 = l0[2 * p :]

        r, w_x, w_y, xc, yc = x0
        # ### Symbolics Sympy ###
        X, Y, Z, R, WX, WY, XC, YC = sym.symbols("X Y Z R WX WY XC YC")

        B_sym = compB_sym()
        b = sym.lambdify((X, Y, Z, R, WX, WY, XC, YC), B_sym, "numpy")
        index_i = np.tile(np.arange(0, p), 3)  # Index Row
        index_j = np.arange(0, 3 * p)  # Index Column
        B_vals = np.array(
            [
                b(x, y, z, r, w_x, w_y, xc, yc).flatten()
                for x, y, z in zip(X0, Y0, Z0)
            ]
        )  # shape (3, p)
        b_vals = B_vals.flatten("F")
        # Create sparse matrix
        B = sp.csr_matrix((b_vals, (index_i, index_j)), shape=(p, 3 * p))

        return B

    def print_results(self) -> None:

        print(
            (
                " ____________________________________________________________________________\n"
                "| \n"
                f"| {Style.BRIGHT}{Fore.MAGENTA}{'Least-squares Results'}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- Number of iterations:        '+ str(self.it_counter)}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- x:                           ' + str(self.normal)}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- v*v^T [mm]:                  '}{np.dot(self.v, self.v)*1000:.4f}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- mean (p2c) [mm]:             '}{np.mean(self.w) * 1000:.4f}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- std (p2c) [mm]:              '}{np.std(self.w) * 1000:.4f}{Style.RESET_ALL}\n"
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
            c=self.w * 1000,
            cmap="viridis",
        )
        plt.colorbar(sc, label="Distances [mm]")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.set_title("Point cloud colored by point-to-cylinder distance")
        plt.grid(True)
        plt.axis("equal")
        plt.show()

        # Plot histogram of the point-to-plane distances
        plt.figure()
        plt.hist(self.w * 1000, bins=100)
        plt.xlabel("Distances in [mm]")
        plt.ylabel("Counts")
        plt.grid()
        plt.title("Histogram of point-to-cylinder distances")
        plt.show()
