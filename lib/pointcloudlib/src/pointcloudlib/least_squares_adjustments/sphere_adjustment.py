from typing import Union

import matplotlib.pyplot as plt
import numpy as np
import pyransac3d as pyrsc
import scipy.sparse as sp
import sympy as sym
from colorama import Fore, Style

from pointcloudlib import PointCloud
from pointcloudlib.least_squares_adjustments.estimator import Estimator


def F_sphere(x, y, z, xc, yc, zc, r):
    f = sym.sqrt((x - xc) ** 2 + (y - yc) ** 2 + (z - zc) ** 2) - r
    return f


def compA_sym():
    X, Y, Z, XC, YC, ZC, R = sym.symbols("X Y Z XC YC ZC R")
    F_Y = F_sphere(X, Y, Z, XC, YC, ZC, R)  # Functional Relationship Symbolic
    A_sym = sym.Matrix([F_Y]).jacobian(
        sym.Matrix([XC, YC, ZC, R])
    )  # Designmatrix Symbolic

    return A_sym


def compB_sym():
    X, Y, Z, XC, YC, ZC, R = sym.symbols("X Y Z XC YC ZC R")
    F_Y = F_sphere(X, Y, Z, XC, YC, ZC, R)  # Functional Relationship Symbolic
    B_sym = sym.Matrix([F_Y]).jacobian(
        sym.Matrix([X, Y, Z])
    )  # Designmatrix Symbolic

    return B_sym


class SphereAdjustment(Estimator):
    def __init__(
        self,
        pc: Union[PointCloud, None] = None,
        initialParams: Union[np.ndarray, None] = None,
        params: Union[np.ndarray, None] = None,
        v: Union[np.ndarray, None] = None,
        w: Union[np.ndarray, None] = None,
        it_counter: Union[int, None] = 0,
        maxIter: Union[int, None] = 50,
        epsilon: Union[float, None] = 1e-08,
        center: Union[np.ndarray, None] = None,
        radius: Union[float, None] = None,
    ):
        super().__init__(
            pc, initialParams, params, v, w, it_counter, maxIter, epsilon
        )  # Estimator
        # self.epsilon = 3e-03
        self.center = None
        self.radius = None

    def computeInitialGuess(self):
        XYZ = self.pc.xyz
        center, radius, _ = pyrsc.Sphere().fit(
            XYZ, thresh=3.0e-03, maxIteration=5000
        )
        self.initialParams = np.r_[center, radius]

        return

    def discrepancies(self, l0, x0):
        p = self.pc.xyz.shape[0]
        X0 = l0[0:p]
        Y0 = l0[p : 2 * p]
        Z0 = l0[2 * p :]

        x_c, y_c, z_c, r = x0

        return np.sqrt((X0 - x_c) ** 2 + (Y0 - y_c) ** 2 + (Z0 - z_c) ** 2) - r

    def designmatrix(self, l0, x0):
        p = self.pc.xyz.shape[0]

        X0 = l0[0:p]
        Y0 = l0[p : 2 * p]
        Z0 = l0[2 * p :]

        xc, yc, zc, r = x0

        # ### Symbolics Sympy ###
        X, Y, Z, XC, YC, ZC, R = sym.symbols("X Y Z XC YC ZC R")

        A_sym = compA_sym()
        a = sym.lambdify((X, Y, Z, XC, YC, ZC, R), A_sym, "numpy")
        A_vals = [a(x, y, z, xc, yc, zc, r) for x, y, z in zip(X0, Y0, Z0)]
        A = np.concatenate(A_vals, axis=0)

        return A

    def conditionmatrix(self, l0, x0):
        p = self.pc.xyz.shape[0]

        X0 = l0[0:p]
        Y0 = l0[p : 2 * p]
        Z0 = l0[2 * p :]
        xc, yc, zc, r = x0

        # ### Symbolics Sympy ###
        X, Y, Z, XC, YC, ZC, R = sym.symbols("X Y Z XC YC ZC R")
        B_sym = compB_sym()
        b = sym.lambdify((X, Y, Z, XC, YC, ZC, R), B_sym, "numpy")
        index_i = np.tile(np.arange(0, p), 3)  # Index Row
        index_j = np.arange(0, 3 * p)  # Index Column
        B_vals = np.array(
            [
                b(x, y, z, xc, yc, zc, r).flatten()
                for x, y, z in zip(X0, Y0, Z0)
            ]
        )  # shape (3, p)
        b_vals = B_vals.flatten("F")
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
                f"| {Style.BRIGHT}{Fore.WHITE}{'- mean (p2s) [mm]:             '}{np.mean(self.w) * 1000:.4f}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- std (p2s) [mm]:              '}{np.std(self.w) * 1000:.4f}{Style.RESET_ALL}\n"
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
        ax.set_title("Point cloud colored by point-to-plane distance")
        plt.grid(True)
        plt.axis("equal")
        plt.show()

        # Plot histogram of the point-to-plane distances
        plt.figure()
        plt.hist(self.w * 1000, bins=100)
        plt.xlabel("Distances in [mm]")
        plt.ylabel("Counts")
        plt.grid()
        plt.title("Histogram of point-to-plane distances")
        plt.show()

    def run(self):
        super().run()
        self.center = self.params[:3]
        self.radius = self.params[3]

    # def F_cylinder(x,y,z,r,w_x,w_y,x0,y0):
    #     # Functional Relationship of a Cylinder in 3D
    #     f = ( ((y-y0)*cos(w_x) + (x-x0)*sin(w_x)*sin(w_y) + z*sin(w_x)*cos(w_y))/r)**2 + (((x-x0)*cos(w_y) - z*sin(w_y))/r)**2 - 1
    #     return f

    # def getFAB_plane(l0,p0):
    # n_x = p0[0]
    # n_y = p0[1]
    # n_z = p0[2]

    # x = l0[0::3]
    # y = l0[1::3]
    # z = l0[2::3]

    # n = x.size

    # ### Symbolics Sympy ###
    # X,Y,Z,N_X,N_Y,N_Z = symbols('X Y Z N_X N_Y N_Z')

    # F_Y = F_plane(X,Y,Z,N_X,N_Y,N_Z)                                  # Functional Relationship Symbolic
    # A_sym = Matrix([F_Y]).jacobian(Matrix([N_X,N_Y,N_Z]))       # Designmatrix Symbolic
    # B_sym = Matrix([F_Y]).jacobian(Matrix([X,Y,Z]))                 # Condition Matrix Symbolic

    # ### Evaluate Sympy ###
    # # Functional Relationship
    # f = lambdify((X,Y,Z,N_X,N_Y,N_Z),F_Y,"numpy")
    # f_y = f(x,y,z,n_x,n_y,n_z)

    # # Designmatrix
    # A = np.c_[x,y,z]

    # # Condition Matrix
    # index_i = np.repeat(np.arange(0,n),(3,))                # Index Row
    # index_j = np.arange(0,3*n)                              # Index Column

    # b = np.tile(np.array([n_x,n_y,n_z]),(n,))
    # B = sparse.csr_matrix((b,(index_i,index_j)),shape=(n,3*n))

    # return f_y,A,B
