from enum import IntEnum
import numpy as np


class VerboseLevel(IntEnum):
    """Verbosity levels for console output"""

    SILENT = 0  # No output
    ERROR = 1  # Only error messages
    WARNING = 2  # Warnings and errors
    INFO = 3  # General status messages
    DEBUG = 4  # Detailed technical information


class RotMat:
    """Class for rotation matrix operations."""

    @staticmethod
    def x(alpha):
        return np.array(
            [
                [1, 0, 0],
                [0, np.cos(alpha), -np.sin(alpha)],
                [0, np.sin(alpha), np.cos(alpha)],
            ]
        )

    @staticmethod
    def y(beta):
        return np.array(
            [
                [np.cos(beta), 0, np.sin(beta)],
                [0, 1, 0],
                [-np.sin(beta), 0, np.cos(beta)],
            ]
        )

    @staticmethod
    def z(gamma):
        return np.array(
            [
                [np.cos(gamma), -np.sin(gamma), 0],
                [np.sin(gamma), np.cos(gamma), 0],
                [0, 0, 1],
            ]
        )

    @staticmethod
    def from_euler(roll: float, pitch: float, yaw: float) -> np.ndarray:
        """Convert Euler angles to rotation matrix.

        Args:
            roll (float): Rotation angle around the X-axis in radians.
            pitch (float): Rotation angle around the Y-axis in radians.
            yaw (float): Rotation angle around the Z-axis in radians.

        Returns:
            np.ndarray: Rotation matrix corresponding to the given Euler angles.
        """  # noqa E501

        R = RotMat.z(yaw) @ RotMat.y(pitch) @ RotMat.x(roll)

        return R

    @staticmethod
    def to_euler(rotmat: np.ndarray) -> np.ndarray:
        """Convert rotation matrix to Euler angles.

        Args:
            rotmat (np.ndarray): Rotation matrix.

        Returns:
            np.ndarray: Euler angles corresponding to the given rotation matrix.
        """  # noqa E501

        rX = np.arctan2(rotmat[2, 1], rotmat[2, 2])

        rY = np.arctan2(
            -rotmat[2, 0], np.sqrt(rotmat[2, 1] ** 2 + rotmat[2, 2] ** 2)
        )

        rZ = np.arctan2(rotmat[1, 0], rotmat[0, 0])

        return np.array([rX, rY, rZ])
