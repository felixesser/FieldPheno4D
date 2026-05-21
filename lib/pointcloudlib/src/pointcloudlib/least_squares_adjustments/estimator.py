from abc import ABC, abstractmethod
from typing import Union

import numpy as np
import scipy.linalg as la
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from colorama import Fore, Style

from pointcloudlib import PointCloud
from pointcloudlib.utils import VerboseLevel

class Estimator(ABC):
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
    ):

        self.pc = pc  # Point cloud object
        self.initialParams = initialParams
        self.params = params
        self.v = v  # Residuals ("Verbesserungen")
        self.w = w
        self.it_counter = it_counter  # Iteration counter of the LS adjustment
        self.maxIter = maxIter
        self.epsilon = epsilon

    @abstractmethod
    def computeInitialGuess(self):
        """
        abstract method for computing initial guess
        """
        pass

    @abstractmethod
    def discrepancies(self, l0, x0):

        pass

    @abstractmethod
    def designmatrix(self, l0, x0):

        pass

    @abstractmethod
    def conditionmatrix(self, l0, x0):

        pass

    def run(self, verbose: int = VerboseLevel.SILENT):

        # Transform the points to local coordinate frame
        # XYZ = self.pc.xyz - np.min(self.pc.xyz, axis=0)
        XYZ = self.pc.xyz
        # Determine dimensions for least-squares
        p = XYZ.shape[
            0
        ]  # number of points (= c: number of condition equations)
        m = p * 3  # number of measurements
        u = 3  # number of parameters
        r = p - u  # redundancy

        # Initial guess parameter with PCA
        if self.initialParams is None:
            self.computeInitialGuess()
        x0 = self.initialParams

        # Measurement vector and stochastic model
        L = np.concatenate(
            (XYZ[:, 0], XYZ[:, 1], XYZ[:, 2])
        )  # Pbservations vector (sorted by x,y,z)
        L0 = L.copy()

        # Covariance matrix (identity)
        S_diag = np.ones(m)
        S = sp.diags(S_diag)
        s0 = 1
        Q = S * (1 / s0**2)

        # Main loop
        isconverged = False

        print(
            (
                " ____________________________________________________________________________"
            )
        )
        print(
            f"| {Style.BRIGHT}{Fore.MAGENTA}Starting Least-Squares Optimization {Style.RESET_ALL}"
        )

        while isconverged == False:
            self.v = L - L0

            A = -self.designmatrix(L0, x0)
            B = self.conditionmatrix(L0, x0)
            W = self.discrepancies(L0, x0)

            # print(np.max(np.abs(W)))

            dL = B @ self.v + W

            # print(np.max(np.abs(dL)))

            # W = -(W + B @ (L - L0))
            M = B @ Q @ B.T  # p x p
            M_csc = M.tocsc()

            # Compute N and U
            N = A.T @ spla.spsolve(M_csc, A)
            U = A.T @ spla.spsolve(M_csc, dL)

            # Solve to estimate parameter vector x
            x = la.solve(N, U)

            # Compute residuals
            v = A @ x - dL

            # print(np.max(np.abs(v)))

            self.v = Q @ B.T @ spla.spsolve(M_csc, v)

            # v_x = self.v[0:p]
            # v_y = self.v[p:2*p]
            # v_z = self.v[2*p:]
            # print(np.max(np.abs(v_x)), np.max(np.abs(v_y)), np.max(np.abs(v_z)))

            # Determine parameter vector and observations
            x_est = x + x0
            L_corr = L + self.v

            # Check for convergence or max iteration
            if (
                np.max(np.abs(x)) < self.epsilon
                or self.it_counter > self.maxIter
            ):
                isconverged = True
                if verbose > VerboseLevel.SILENT:
                    print(
                        f"| {Style.BRIGHT}{Fore.GREEN}Converged! {Style.RESET_ALL}"
                    )
            else:
                # Update parameter vector and observations
                x0 = x_est
                L0 = L_corr.copy()

                # Point cloud from L0 and visualize
                # X = L0[0:p]
                # Y = L0[p:2*p]
                # Z = L0[2*p:]
                # XYZ = np.c_[X, Y, Z]
                # pc_test = pointcloud(xyz=XYZ)
                # pc_test.intensity = self.v[0:p]
                # pc_test.plot(scalarfield="intensity" )

                # Print some useful information about the current iteration
                if verbose > VerboseLevel.DEBUG:
                    print(
                        f"| {Style.BRIGHT}{Fore.WHITE}Iteration: {self.it_counter:01}, v_squared: {np.dot(self.v, self.v):.4f}, dx: {x}{Style.RESET_ALL}"
                    )
                self.it_counter += 1

        # end while main
        if verbose > VerboseLevel.SILENT:
            print(
                (
                    "|____________________________________________________________________________"
                )
            )

        self.w = self.discrepancies(L, x_est)
        self.params = x_est
        # self.pc.shiftxyz(offset)

    @abstractmethod
    def print_results(self) -> None:
        pass

    @abstractmethod
    def visualize_results(self) -> None:
        pass
