import copy
import datetime
import os
import random
from pathlib import Path
from typing import Union

import laspy
import numpy as np
import open3d as o3d
import pandas as pd
from colorama import Fore, Style
from plyfile import PlyData
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors

from pointcloudlib.utils import VerboseLevel


class PointCloud:
    """Point cloud class for storing and processing 3D point cloud data.

    Attributes:
        time      (np.ndarray): Time information of the points.
        xyz       (np.ndarray): XYZ coordinates of the points.
        intensity (np.ndarray): Intensity values of the points.
        color     (np.ndarray): RGB color values of the points.
                                Defined in range [0, 1].
        normals   (np.ndarray): Normal vectors of the points.
        bbox      (np.ndarray): Bounding box of the point cloud.
        txyz      (np.ndarray): Center of the point cloud.
        scalarfields    (dict): Dictionary to store additional scalar fields.
    """

    # region Attributes

    time: np.ndarray
    _xyz: np.ndarray
    intensity: np.ndarray
    color: np.ndarray  # Defined in range [0, 1]
    normals: np.ndarray
    txyz: np.ndarray
    bbox: (
        np.ndarray
    )  # [x_min, x_max, y_min, y_max], its just in 2D at the moment
    scalarfields: dict
    neighbors_n: NearestNeighbors  # n nearest neighbors (n: number of neighbors)  # noqa: E501
    neighbors_r: NearestNeighbors  # neareat neighbors with in radius (r: radius to search neighbors)  # noqa: E501

    GPS_LEAP_SECONDS = 18
    GPS_WEEK_ZERO = datetime.datetime(
        1980, 1, 6, 0, 0, 0, tzinfo=datetime.timezone.utc
    )

    @property
    def count(self) -> int:
        """Get the number of points in the point cloud.

        Returns:
            int: Number of points.
        """

        if self._xyz is None:
            return 0

        return self._xyz.shape[0]

    @property
    def has_time(self) -> bool:
        """Check if the point cloud has time information.

        Returns:
            bool: True if time information is present, False otherwise.
        """

        return self.time is not None

    @property
    def has_intensity(self) -> bool:
        """Check if the point cloud has intensity values.

        Returns:
            bool: True if intensity values are present, False otherwise.
        """

        return self.intensity is not None

    @property
    def has_color(self) -> bool:
        """Check if the point cloud has color values.

        Returns:
            bool: True if color values are present, False otherwise.
        """

        return self.color is not None

    @property
    def has_normals(self) -> bool:
        """Check if the point cloud has normal vectors.

        Returns:
            bool: True if normal vectors are present, False otherwise.
        """

        return self.normals is not None

    @property
    def xyz(self) -> np.ndarray:
        """Get the XYZ coordinates of the point cloud.

        Returns:
            np.ndarray: XYZ coordinates of the points.
        """

        return self._xyz

    @xyz.setter
    def xyz(self, value: np.ndarray) -> None:
        """Set the XYZ coordinates of the point cloud.

        Args:
            value (np.ndarray): New XYZ coordinates to set.
        """

        self._xyz = value

        self.bbox = self._get_bounding_box()
        self.txyz = self._get_center()

    # endregion Attributes

    # region Core Methods

    def __init__(
        self,
        time: Union[np.ndarray, None] = None,
        xyz: Union[np.ndarray, None] = None,
        intensity: Union[np.ndarray, None] = None,
        color: Union[np.ndarray, None] = None,
        normals: Union[np.ndarray, None] = None,
        txyz: Union[np.ndarray, None] = None,
        bbox: Union[np.ndarray, None] = None,
        scalarfields: Union[dict] = {},
        neighbors: Union[NearestNeighbors] = None,
    ):

        self.time = time
        self._xyz = xyz
        self.intensity = intensity
        self.color = color
        self.normals = normals
        self.txyz = txyz
        self.bbox = bbox
        self.scalarfields = copy.deepcopy(scalarfields)
        self.neighbors = neighbors

        if self.xyz is None:
            return

        if self.txyz is None:
            self.txyz = self._get_center()

        if self.bbox is None:
            self.bbox = self._get_bounding_box()

    def __str__(self) -> str:
        """
        Returns string describing trajectory
        """
        width = 24
        return (
            f"\n _______________________________________________________\n"
            f"| ------------------ Point Cloud Info ------------------- |\n"
            f"| Number of points:              {self.count:<{width}}|\n"
            f"|_______________________________________________________|\n"
        )

    def copy(self) -> "PointCloud":
        """Returns a copy of the instance

        Returns:
            PointCloud: A copy of the point cloud instance
        """

        return copy.deepcopy(self)

    # endregion

    # region I/O Methods

    def read(
        self,
        fname: str,
        metadata: dict[str, any] | None = None,
        verbose: int = VerboseLevel.SILENT,
    ) -> None:
        """Read point clouds from different filestypes

        Currently supported:
            - .las (with laspy)
            - .ply (with plyfile)
            - .csv (with pandas)
            - .txt (not fully implemented yet)

        Raises:
            ValueError: If the file format is unsupported.

        Args:
            fname (str): Filename of the point cloud file.
            metadata (dict[str, any], optional): Metadata for reading csv files. Defaults to None. Only used for csv files and should only contain the following keys:
                - fields (list[str]): Orderd list of field names in the csv file. The field names have to be one of the following:
                    - d: Day information (required if t is used)
                    - t: Time information (required if d is used)
                    - dt: Datetime information (if dt is used, d and t are ignored)
                    - x, y, z: XYZ coordinate information
                    - i (optional): Intensity information
                    - s (optional): Scalar field information (multiple scalar fields can be included)
                    - -: Placeholder for fields that are not used
                - delimiter (str, optional): Delimiter used in the csv file (e.g., " ", ",", ";"). Defaults to " ".
                - time_format (str, optional): Format of the time information in the csv file (unix, datetime, or gps_sow). Defaults to "unix".
                - time_offset (float, optional): Time offset (in seconds) to apply to the time information. Defaults to 0.0.
                - timezone (str, optional): Timezone of the datetime information in the csv file (TZ name or GPS, e.g., "UTC+2"). Only used if time_format is "unix" or "datetime". Defaults to "UTC".
                - datetime_format (str, optional): Format of the datetime information in the csv file (e.g., "%d/%m/%Y %H:%M:%S"). Only used if time_format is "datetime". Defaults to "%d/%m/%Y %H:%M:%S".
                - gps_week (int, optional): GPS week number. Only used if time_format is "gps_sow". Defaults to 0.
                - has_header (bool, optional): Whether the csv file has a header row. Defaults to False.
                - chunksize (int, optional): Number of rows to read at a time when reading the csv file in chunks. Defaults to 100_000_000.
            verbose (int, optional): Verbosity level for logging
                                      (0=silent, 1=error, 2=warning, 3=info, 4=debug).
                                      Defaults to VerboseLevel.SILENT.
        """  # noqa: E501

        # region output (console)

        if verbose > VerboseLevel.SILENT:
            print(
                f"{Style.BRIGHT}{Fore.MAGENTA}"
                "┏" + "━" * 40 + "┓\n"
                f"┃{'Read point cloud from file':^40}┃\n"
                "┗" + "━" * 40 + "┛"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        try:
            str_s = fname.split(".")
            file_extension = str_s[-1]

            # region output (console)

            # Debug output: File information
            if verbose >= VerboseLevel.DEBUG:
                print(
                    f"{Fore.CYAN}[DEBUG] Input parameters\n"
                    f"  - Filename: {fname}\n"
                    f"  - File extension: {file_extension}"
                    f"{Style.RESET_ALL}\n"
                )

            # endregion output (console)

            match file_extension:
                case "las" | "laz":
                    self._read_las(fname, verbose)

                case "ply":
                    self._read_ply(fname, verbose)

                case "csv":
                    if metadata is None:
                        raise ValueError(
                            "Metadata is required for reading CSV files."
                        )
                    self._read_csv(fname, metadata, verbose)

                case "txt":
                    self._read_txt(fname, verbose=verbose)

                case _:
                    # region output (console)

                    if verbose >= VerboseLevel.ERROR:
                        print(
                            f"{Fore.RED}[ERROR] Unsupported file format: "
                            f"{file_extension}"
                            f"{Style.RESET_ALL}\n"
                        )

                    # endregion output (console)

                    raise ValueError(
                        f"Unsupported file format: {file_extension}"
                    )

        except Exception as e:
            # region output (console)

            if verbose >= VerboseLevel.ERROR:
                print(
                    f"{Fore.RED}[ERROR] Failed to read file: "
                    f"{str(e)}"
                    f"{Style.RESET_ALL}\n"
                )

            # endregion output (console)

            raise

        # region output (console)

        if verbose >= VerboseLevel.WARNING:
            if self.count == 0:
                print(
                    f"{Fore.YELLOW}[WARNING] No points loaded from file!"
                    f"{Style.RESET_ALL}\n"
                )
            elif self.count < 100:
                print(
                    f"{Fore.YELLOW}[WARNING] Very few points loaded "
                    f"({self.count} points). Check file integrity."
                    f"{Style.RESET_ALL}\n"
                )

        if verbose >= VerboseLevel.INFO:
            filename_str = str_s[0].split("/")[-1] + "." + str_s[-1]

            numPoints_str = f"{self.count:_.0f}"

            intensity_str = "None"
            if self.has_intensity:
                intensity_str = (
                    f"{self.intensity.min():_.0f}"
                    f" - "
                    f"{self.intensity.max():_.0f}"
                )

            time_range_str = "None"
            time_diff_str = "None"
            if self.has_time:
                time_range_str = f"{self.time[0]:_.3f} - {self.time[-1]:_.3f}"
                time_diff_str = f"{(self.time[-1] - self.time[0]):_.3f}"

            tXYZ_str = (
                f"{self.txyz[0]:_.2f}, "
                f"{self.txyz[1]:_.2f}, "
                f"{self.txyz[2]:_.2f}"
            )

            bBox_1_str = f"{self.bbox[0]:_.2f}, {self.bbox[1]:_.2f}"
            bBox_2_str = f"{self.bbox[2]:_.2f}, {self.bbox[3]:_.2f}"
            bBox_3_str = f"{self.bbox[4]:_.2f}, {self.bbox[5]:_.2f}"

            print(
                f"{Fore.WHITE}"
                f"[INFO] Read point cloud from file\n"
                f"  - filename:      {filename_str}\n"
                f"  - #points:       {numPoints_str}\n"
                f"  - intensities:   {intensity_str}\n"
                f"  - timestamps:    {time_range_str}\n"
                f"                   {time_diff_str}\n"
                f"  - tXYZ:          {tXYZ_str}\n"
                f"  - bBox:          {bBox_1_str}\n"
                f"                   {bBox_2_str}\n"
                f"                   {bBox_3_str}"
                f"{Style.RESET_ALL}\n"
            )

        if verbose >= VerboseLevel.DEBUG:
            print(f"{Fore.CYAN}[DEBUG] Additional information:")

            if self.scalarfields:
                print(
                    f"  - Scalar fields loaded: "
                    f"{list(self.scalarfields.keys())}"
                )

            print(
                f"  - Memory size: "
                f"~{self._get_memory_size():.2f} MB"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

    def _read_las(
        self, fname: str, verbose: int = VerboseLevel.SILENT
    ) -> None:
        """Reads a LAS file and populates the point cloud attributes.

        Args:
            fname   (str):           The filename of the LAS file to read.
            verbose (int, optional): Verbosity level for logging. Defaults to VerboseLevel.SILENT.
        """  # noqa: E501

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG] Starting LAS file read",
                f"{Style.RESET_ALL}\n",
            )

        # endregion output (console)

        las = laspy.read(fname)

        # Get scalar fields of the point cloud
        scfield = []
        for dimension in las.point_format.dimensions:
            scfield.append(dimension.name)

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG] LAS scalar fields found: "
                f"{', '.join(scfield)}"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        # Read points in chunks and accumulate
        xyz_chunks = []
        intensity_chunks = []
        time_chunks = []

        with laspy.open(fname) as las:
            for points in las.chunk_iterator(100_000_000):
                if "X" in scfield:
                    xyz_chunks.append(
                        np.column_stack((points.x, points.y, points.z))
                    )

                if "intensity" in scfield:
                    intensity_chunks.append(points.intensity)

                if "gps_time" in scfield:
                    time_chunks.append(points.gps_time)

        # Concatenate all chunks
        if xyz_chunks:
            self.xyz = np.vstack(xyz_chunks)
        if intensity_chunks:
            self.intensity = np.concatenate(intensity_chunks)
        if time_chunks:
            self.time = np.concatenate(time_chunks)

    def _read_ply(
        self, fname: str, verbose: int = VerboseLevel.SILENT
    ) -> None:
        """Reads a PLY file and populates the point cloud attributes.

        Args:
            fname   (str):           The filename of the PLY file to read.
            verbose (int, optional): Verbosity level for logging. Defaults to VerboseLevel.SILENT.
        """  # noqa: E501

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG] Starting PLY file read",
                f"{Style.RESET_ALL}\n",
            )

        # endregion output (console)

        plydata = PlyData.read(fname)
        vertex_data = plydata["vertex"].data

        # xyz coordinates
        self.xyz = np.column_stack((
            vertex_data["x"],
            vertex_data["y"],
            vertex_data["z"],
        ))

        # time stamps
        self.time = vertex_data["scalar_GpsTime"]

    def _read_txt(
        self,
        fname: str,
        delimiter: str = " ",
        verbose: int = VerboseLevel.SILENT,
    ) -> None:
        """Reads a TXT file and populates the point cloud attributes.

        Args:
            fname   (str):           The filename of the TXT file to read.
            verbose (int, optional): Verbosity level for logging. Defaults to VerboseLevel.SILENT.
        """  # noqa: E501

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG] Starting TXT file read",
                f"{Style.RESET_ALL}\n",
            )

        # endregion output (console)

        self.xyz = np.loadtxt(
            fname, delimiter=delimiter, usecols=[0, 1, 2], comments="#"
        )  # assuming [x, y, z]

        # TODO: Implement reading scalar fields

        # region output (console)

        if verbose >= VerboseLevel.WARNING:
            print(
                f"{Fore.YELLOW}[WARNING] TXT format: "
                f"Scalar fields not yet implemented."
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

    def _read_csv(
        self,
        fname: str,
        metadata: dict[str, any],
        verbose: int = VerboseLevel.SILENT,
    ) -> None:

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG] Starting CSV file read{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        # metadata parsing
        fields: list[str] = metadata["fields"]
        delimiter: str = metadata.get("delimiter", " ")
        time_format: str = metadata.get("time_format", "unix")
        time_offset: float = metadata.get("time_offset", 0.0)
        timezone: str = metadata.get("timezone", "UTC")
        datetime_format: str = metadata.get(
            "datetime_format", "%d/%m/%Y %H:%M:%S"
        )
        gps_week: int = metadata.get("gps_week", 0)
        has_header: bool = metadata.get("has_header", False)
        chunksize: int = metadata.get("chunksize", 100_000_000)

        xyz_chunks: list = []
        intensity_chunks: list = []
        time_chunks: list = []
        scalar_chunks: dict[str, list] = {}

        if delimiter == "\\s":
            delimiter = " "

        # Read points
        for points in pd.read_csv(
            fname,
            sep=delimiter,
            header=0 if has_header else None,
            chunksize=chunksize,
        ):
            if "dt" in fields:
                time_chunks.append(points.iloc[:, fields.index("dt")])

            elif "t" in fields and "d" in fields:
                dates: pd.Series = points.iloc[:, fields.index("d")]
                times: pd.Series = points.iloc[:, fields.index("t")]

                time_chunks.append(dates.str.cat(times, sep=" "))

            else:
                raise ValueError(
                    "Time information is missing. Either 'dt' or both 'd' and 't' fields are required."
                )

            xyz_chunks.append(
                np.column_stack((
                    points.iloc[:, fields.index("x")],
                    points.iloc[:, fields.index("y")],
                    points.iloc[:, fields.index("z")],
                ))
            )

            if "i" in fields:
                intensity_chunks.append(points.iloc[:, fields.index("i")])

            if "s" not in fields:
                continue

            indices: list[int] = [
                i for i, field in enumerate(fields) if field == "s"
            ]

            for idx in indices:
                name = f"Scalar_{idx}"

                if has_header:
                    name = points.columns[idx]

                scalar_chunks.setdefault(name, []).append(points.iloc[:, idx])

        # Concatenate all chunks
        self.xyz = np.vstack(xyz_chunks)

        if "i" in fields:
            self.intensity = np.concatenate(intensity_chunks)

        time_str: np.ndarray = np.concatenate(time_chunks)

        match time_format:
            case "unix":
                self.time = time_str.astype(float) + time_offset

            case "datetime":
                self.time = (
                    pd.to_datetime(
                        time_str, format=datetime_format, utc=True
                    ).astype(np.int64)
                    / 1e9
                    + time_offset
                )

            case "gps_sow":
                self.time = (
                    time_str.astype(float).astype(float).flatten()
                    + gps_week * 604800
                    - self.GPS_LEAP_SECONDS
                    + self.GPS_WEEK_ZERO.timestamp()
                    + time_offset
                )

            case _:
                raise ValueError(f"Unsupported time format: {time_format}")

        if time_format != "gps_sow":
            if timezone == "GPS":
                self.time -= self.GPS_LEAP_SECONDS

            if timezone != "UTC":
                tz_offset_str: str = timezone.replace("UTC", "")
                tz_offset: int = int(tz_offset_str[1:]) * 3600

                if tz_offset_str[0] == "+":
                    tz_offset *= -1

                self.time += tz_offset

        for key, chunks in scalar_chunks.items():
            self.scalarfields[key] = np.concatenate(chunks)

    def write(self, fname: str, verbose: int = VerboseLevel.SILENT) -> None:
        """Write point clouds to different filestypes

        Currently supported:
            - .las (with laspy)
            - .txt (with numpy)

        Raises:
            ValueError: If the file format is unsupported.

        Args:
            fname   (str):           The filename to write to
            verbose (int, optional): Verbosity level for logging. Defaults to VerboseLevel.SILENT.
        """  # noqa: E501

        # region output (console)

        if verbose > VerboseLevel.SILENT:
            print(
                f"{Style.BRIGHT}{Fore.MAGENTA}"
                "┏" + "━" * 40 + "┓\n"
                f"┃{'Write point cloud to file':^40}┃\n"
                "┗" + "━" * 40 + "┛"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        try:
            str_s = fname.split(".")

            file_extension = str_s[-1]

            match file_extension:
                case "las" | "laz":
                    header = laspy.LasHeader(point_format=3, version="1.2")

            header.offsets = self.txyz

            for key, _ in self.scalarfields.items():
                header.add_extra_dim(
                    laspy.ExtraBytesParams(name=key, type=np.float64)
                )

            header.scales = np.array([0.0001, 0.0001, 0.0001])

            las = laspy.LasData(header)

            las.x = self._xyz[:, 0]
            las.y = self._xyz[:, 1]
            las.z = self._xyz[:, 2]

            if self.has_intensity:
                las.intensity = self.intensity

            if self.has_time:
                las.gps_time = self.time

            # check for scalar fields
            if self.scalarfields is not None and len(self.scalarfields) > 0:
                # Add scalar fields
                for key, value in self.scalarfields.items():
                    setattr(las, key, value)

            las.write(fname)
        except Exception as e:
            # region output (console)

            if verbose >= VerboseLevel.ERROR:
                print(
                    f"{Fore.RED}[ERROR] Failed to write file: "
                    f"{str(e)}"
                    f"{Style.RESET_ALL}\n"
                )

            # endregion output (console)

            raise

    def _write_txt(
        self, fname: str, verbose: int = VerboseLevel.SILENT
    ) -> None:
        """Writes a TXT file from the point cloud attributes.

        Args:
            fname   (str):           The filename of the TXT file to write.
            verbose (int, optional): Verbosity level for logging. Defaults to VerboseLevel.SILENT.
        """  # noqa: E501

        # region output (console)

        if verbose >= VerboseLevel.INFO:
            print(
                f"{Fore.WHITE}[INFO] Starting TXT file writing"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        formats = ["%10.8f", "%10.5f", "%10.5f", "%10.5f", "%10.2f"]
        np.savetxt(
            fname,
            np.c_[self.time, self._xyz, self.intensity],
            fmt=formats,
        )

    # endregion I/O Methods

    # region Private Methods

    def _get_bounding_box(self) -> np.ndarray:
        """Computes the 3D bounding of the point cloud

        Returns:
            np.ndarray: Bounding box coordinates
                        (min_x, max_x, min_y, max_y, min_z, max_z)
        """

        if self._xyz is None:
            return None

        if self.count == 0:
            return np.empty((0, 6))

        return np.array([
            np.min(self._xyz[:, 0]),
            np.max(self._xyz[:, 0]),
            np.min(self._xyz[:, 1]),
            np.max(self._xyz[:, 1]),
            np.min(self._xyz[:, 2]),
            np.max(self._xyz[:, 2]),
        ])

    def _get_center(self) -> np.ndarray:
        """Computes the center of the point cloud

        Returns:
            np.ndarray: Center coordinates
                        (x_center, y_center, z_center)
        """

        if self._xyz is None:
            return None

        if self.count == 0:
            return np.empty((0, 3))

        return np.array([
            np.mean(self._xyz[:, 0]),
            np.mean(self._xyz[:, 1]),
            np.mean(self._xyz[:, 2]),
        ])

    def _get_memory_size(self) -> float:
        """Computes the memory size of the point cloud object in MB

        Returns:
            float: Memory size in MB
        """

        size = 0

        # Iterate over all instance attributes
        for _, attr_value in self.__dict__.items():
            if attr_value is None:
                continue

            # Handle dictionaries (like scalarfields)
            if isinstance(attr_value, dict):
                # Add dictionary overhead
                size += attr_value.__sizeof__()

                # Add size of numpy arrays within the dictionary
                for dict_value in attr_value.values():
                    if dict_value is None:
                        continue

                    if hasattr(dict_value, "nbytes"):
                        size += dict_value.nbytes

            # Add size if attribute has nbytes (numpy arrays)
            elif hasattr(attr_value, "nbytes"):
                size += attr_value.nbytes

        return size / 1024 / 1024

    # endregion Private Methods

    # region Scalarfields

    def add_scalarfield(self, X: np.ndarray, name: str) -> None:
        """Adds a scalarfield (X) to the point cloud object
        with the name specified

        Args:
            X (np.ndarray): Scalar field data
            name (str): Name of the scalar field
        """

        self.scalarfields[name] = X

    def get_scalarfield(self, name: str) -> np.ndarray:
        """Gets a scalarfield from the point cloud object

        Args:
            name (str): Name of the scalar field to get

        Returns:
            np.ndarray: Scalar field data
        """

        if name in self.scalarfields:
            return self.scalarfields[name]
        else:
            return None

    def remove_scalarfield(self, name: str) -> None:
        """Removes a scalarfield from the point cloud object

        Args:
            name (str): Name of the scalar field to remove
        """

        if name in self.scalarfields:
            del self.scalarfields[name]

    def print_scalarfields(self) -> None:
        """Prints all scalar fields and their values"""

        for key, value in self.scalarfields.items():
            print(f"{key}: {value}")

    # endregion Scalarfields

    # region NearestNeighbors

    def compute_nearest_neighbor(
        self, n_neighbors: int = 1, algorithm: str = "auto"
    ) -> None:
        """Computes the nearest neighbor points

        Args:
            n_neighbors (int): number of neighbors to determine
            algorithm (str): algorithm used to determine nearest neighbors
        """

        self.neighbors_n = NearestNeighbors(
            n_neighbors=n_neighbors, algorithm=algorithm
        ).fit(self.xyz)

    def compute_neighbors_within_radius(
        self, radius: float = 1, algorithm: str = "auto"
    ) -> "NearestNeighbors":
        """Computes the nearest neighbor points with a radius query

        Args:
            radius (float): radius to search with
            algorithm (str): algorithm used to determine nearest neighbors
        """

        self.neighbors_r = NearestNeighbors(
            radius=radius, algorithm=algorithm
        ).fit(self.xyz)

    # endregion NearestNeighbors

    # region get / set Points

    def select_by_index(self, idx: np.ndarray) -> "PointCloud":
        """Select points with indices

        Args:
            idx (np.ndarray): Indices of the points to select

        Returns:
            PointCloud: New point cloud object with selected points
        """

        pc = PointCloud()

        pc.xyz = self._xyz[idx, :]

        if self.has_intensity:
            pc.intensity = self.intensity[idx]
        if self.has_time:
            pc.time = self.time[idx]
        if self.has_normals:
            pc.normals = self.normals[idx, :]
        if self.has_color:
            pc.color = self.color[idx, :]

        # indexing scalarfields
        for key, _ in self.scalarfields.items():
            pc.scalarfields[key] = self.scalarfields[key][idx]

        return pc

    def select_by_bbox(
        self, bbox: np.ndarray
    ) -> tuple["PointCloud", np.ndarray]:
        """Select points within a bounding box

        The method selects the indices of points that lie within the specified bounding box
        and uses the select_by_index method to create a new point cloud object.

        Args:
            bbox (np.ndarray): Bounding box coordinates
                               (min_x, max_x, min_y, max_y, min_z, max_z)

        Returns:
            A tuple containing:
            - PointCloud: New point cloud object with points within the bounding box
            - np.ndarray: Indices of the points within the bounding box
        """  # noqa: E501

        mask = (
            (bbox[0] <= self._xyz[:, 0])
            & (self._xyz[:, 0] <= bbox[1])
            & (bbox[2] <= self._xyz[:, 1])
            & (self._xyz[:, 1] <= bbox[3])
            & (bbox[4] <= self._xyz[:, 2])
            & (self._xyz[:, 2] <= bbox[5])
        )

        indices = np.where(mask)[0]

        pc = self.select_by_index(indices)

        return pc, indices

    def insert(
        self,
        xyz: Union[np.ndarray, None] = None,
        time: Union[np.ndarray, None] = None,
        intensity: Union[np.ndarray, None] = None,
        idxA=None,
        idxB=None,
        update_bounding_box: bool = True,
        update_center: bool = True,
    ) -> None:
        """Inserts points at a specific index of an existing pointcloud object

        Args:
            xyz (Union[np.ndarray, None], optional): Point cloud coordinates. Defaults to None.
            time (Union[np.ndarray, None], optional): Point cloud timestamps. Defaults to None.
            intensity (Union[np.ndarray, None], optional): Point cloud intensities. Defaults to None.
            idxA (Union[int, None], optional): Start index for insertion. Defaults to None.
            idxB (Union[int, None], optional): End index for insertion. Defaults to None.
        """  # noqa: E501

        if time is not None:
            self.time[idxA:idxB] = time

        if xyz is not None:
            self._xyz[idxA:idxB] = xyz

            if update_bounding_box:
                self.bbox = self._get_bounding_box()

            if update_center:
                self.txyz = self._get_center()

        if intensity is not None:
            self.intensity[idxA:idxB] = intensity

    # endregion get / set Points

    # region subsample

    def subsample(
        self,
        method: str = "space",
        factor: float = 1,
        voxel_size: float = None,
        verbose: int = VerboseLevel.SILENT,
    ) -> tuple["PointCloud", np.ndarray]:
        """Subsamples the point cloud

        Currently supported methods:
            - 'space':        _subsample_space Method.
            - 'random':       _subsample_random Method.
            - 'voxelAverage': _subsample_voxel_average Method (Requires voxel_size parameter)
            - 'voxelRandom':  _subsample_voxel_random Method (Requires voxel_size parameter)

        Args:
            method       (str,   optional): Subsampling method
                                            ('space', 'random', 'voxelAverage', 'voxelRandom').
                                            Default is 'space'.
            factor       (float, optional): Subsampling factor. Default is 1 (no subsampling).
                                            Required if method is 'space' or 'random'.
            voxel_size   (float, optional): Voxel size for voxel subsampling.
                                            Required if method is 'voxel'.
            verbose      (int,   optional): Verbosity level for logging
                                            (0=silent, 1=error, 2=warning, 3=info, 4=debug).
                                            Defaults to VerboseLevel.SILENT.

        Raises:
            ValueError: If the subsampling method is not recognized
            ValueError: If voxel size is not specified for voxel subsampling

        Returns:
            tuple: A tuple containing:
                - PointCloud: The subsampled point cloud.
                - np.ndarray: Indices of inlier points retained in the filtered point cloud.
        """  # noqa: E501

        # region output (console)

        if verbose > VerboseLevel.SILENT:
            print(
                f"{Style.BRIGHT}{Fore.MAGENTA}"
                "┏" + "━" * 40 + "┓\n"
                f"┃{'Point cloud subsampling':^40}┃\n"
                "┗" + "━" * 40 + "┛"
                f"{Style.RESET_ALL}\n"
            )

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG] Input parameters\n"
                f"  - Method: '{method}'\n"
                f"  - Factor: {factor}\n"
                f"  - Voxel size: {voxel_size}"
                f"{Style.RESET_ALL}\n"
            )

        match method:
            case "voxelAverage" | "voxelRandom":
                if voxel_size is None:
                    raise ValueError(
                        "Voxel size must be specified for voxel subsampling!"
                    )

        # endregion output (console)

        # Create point cloud object
        pc_out = PointCloud()

        match method:
            case "space":
                pc_out, indices = self._subsample_space(factor, verbose)

            case "random":
                pc_out, indices = self._subsample_random(factor, verbose)

            case "voxelAverage":
                pc_out, indices = self._subsample_voxel_average(
                    voxel_size, verbose
                )

            case "voxelRandom":
                pc_out, indices = self._subsample_voxel_random(
                    voxel_size, verbose
                )

            case _:
                raise ValueError(
                    f"Subsampling method '{method}' not recognized!"
                )

        # region output (console)

        points_before = self.count
        points_after = pc_out.count
        points_percent = (points_after / points_before) * 100

        if verbose >= VerboseLevel.ERROR:
            if points_after == 0:
                print(
                    f"{Fore.YELLOW}[WARNING] All points removed! "
                    f"Check file integrity."
                    f"{Style.RESET_ALL}\n"
                )

        if verbose >= VerboseLevel.WARNING:
            if points_percent < 1:
                print(
                    f"{Fore.YELLOW}[WARNING] Many points removed "
                    f"({points_after:_} points)."
                    f"{Style.RESET_ALL}\n"
                )

        if verbose >= VerboseLevel.INFO:
            print(
                f"{Fore.WHITE}"
                f"[INFO] Point cloud subsampled\n"
                f"  - Method:             {method}\n"
                f"  - #points before:     {points_before:_}\n"
                f"  - #points afterwards: {points_after:_}\n"
                f"  - Percentage kept:    {points_percent:.2f} %"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        return pc_out, indices

    def _subsample_space(
        self, factor: float, verbose: int = VerboseLevel.SILENT
    ) -> tuple["PointCloud", np.ndarray]:
        """Subsamples the point cloud in space by a given factor.

        Subsamples points based on a fixed index interval.

        Args:
            factor  (float):         The subsampling factor.
            verbose (int, optional): Verbosity level for logging. Defaults to VerboseLevel.SILENT.

        Returns:
            tuple: A tuple containing:
                - PointCloud: The subsampled point cloud.
                - np.ndarray: Indices of inlier points retained in the filtered point cloud.
        """  # noqa: E501

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG]"
                f" Space subsampling details\n"
                f"  - Input points: {self.count:_}\n"
                f"  - Factor: {factor}"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        # Compute indices
        indices = np.arange(start=0, stop=self.count, step=factor)

        pc_out = self.select_by_index(indices)

        return pc_out, indices

    def _subsample_random(
        self, factor: float, verbose: int = VerboseLevel.SILENT
    ) -> tuple["PointCloud", np.ndarray]:
        """Subsamples the point cloud randomly by a given factor.

        Randomly selects a subset of points.

        Args:
            factor  (float):         The subsampling factor.
            verbose (int, optional): Verbosity level for logging. Defaults to VerboseLevel.SILENT.

        Returns:
            tuple: A tuple containing:
                - PointCloud: The subsampled point cloud.
                - np.ndarray: Indices of inlier points retained in the filtered point cloud.
        """  # noqa: E501

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG]"
                f" Random subsampling details\n"
                f"  - Input points: {self.count:_}\n"
                f"  - Factor: {factor}"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        # Determine number of points
        N = int(self.count / factor)

        # Get random indices
        indices = random.sample(range(1, self.count), N)

        pc_out = self.select_by_index(indices)

        return pc_out, indices

    def _subsample_voxel_average(
        self, voxel_size: float, verbose: int = VerboseLevel.SILENT
    ) -> tuple["PointCloud", np.ndarray]:
        """Subsamples the point cloud using voxel averaging.

        Uses voxel grid filtering (open3D/voxel_down_sample) to downsample the point cloud.
        Points within the same voxel are merged to a single point in the output voxel.

        Args:
            voxel_size (float):         The size of the voxel for subsampling.
            verbose    (int, optional): Verbosity level for logging. Defaults to VerboseLevel.SILENT.

        Returns:
            tuple: A tuple containing:
                - PointCloud: The subsampled point cloud.
                - np.ndarray: Indices of inlier points retained in the filtered point cloud.
        """  # noqa: E501

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG]"
                f" Voxel average subsampling details\n"
                f"  - Input points: {self.count:_}\n"
                f"  - Voxel size: {voxel_size}\n"
                f"  - Has normals: {self.has_normals}\n"
                f"  - Has intensity: {self.has_intensity}\n"
                f"  - Has colors: {self.has_color}\n"
                f"  - Scalar fields: {list(self.scalarfields.keys())}"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        # region Convert to Open3D point cloud

        pc_in = o3d.geometry.PointCloud()
        pc_in.points = o3d.utility.Vector3dVector(self._xyz - self.txyz)

        # Add normals if available
        if self.has_normals:
            pc_in.normals = o3d.utility.Vector3dVector(self.normals)

        # Add intensity if available
        if self.has_intensity:
            intensity_max = np.max(self.intensity)
            intensity_normalized = self.intensity / intensity_max
            pc_in.colors = o3d.utility.Vector3dVector(
                np.column_stack([intensity_normalized] * 3)
            )

            # region output (console)

            if verbose >= VerboseLevel.DEBUG:
                intensity_min = np.min(self.intensity)

                print(
                    f"{Fore.CYAN}[DEBUG] Intensity processing\n"
                    f"  - Max intensity: {intensity_max:.2f}\n"
                    f"  - Min intensity: {intensity_min:.2f}\n"
                    f"  - Normalized range: [0.0, 1.0]"
                    f"{Style.RESET_ALL}\n"
                )

            # endregion output (console)

        # endregion Convert to Open3D point cloud

        pc, indices, _ = pc_in.voxel_down_sample_and_trace(
            voxel_size=voxel_size,
            min_bound=pc_in.get_min_bound(),
            max_bound=pc_in.get_max_bound(),
            approximate_class=False,
        )

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG] Voxel downsampling results\n"
                f"  - Output voxels: {indices.shape[0]:_}\n"
                f"  - Max points per voxel: {indices.shape[1]}"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        # region Convert back to PointCloud object

        pc_out = PointCloud()
        pc_out.xyz = np.asarray(pc.points) + self.txyz

        if self.has_intensity:
            pc_out.intensity = np.asarray(pc.colors)[:, 0] * intensity_max

        if self.has_normals:
            pc_out.normals = np.asarray(pc.normals)

        # endregion Convert back to PointCloud object

        # region averaging not supported (o3d) parameters

        sf_keys = self.scalarfields.keys()

        if len(sf_keys) > 0:
            # region output (console)

            if verbose >= VerboseLevel.DEBUG:
                print(
                    f"{Fore.CYAN}[DEBUG] Processing scalar fields: "
                    f"{list(sf_keys)}"
                    f"{Style.RESET_ALL}\n"
                )

            # endregion output (console)

            # Initialize dictionary for mean scalar fields
            num_voxels = len(indices)
            for key in sf_keys:
                pc_out.scalarfields[key] = np.zeros(num_voxels)

            # Compute mean scalar field for each voxel
            for i, voxel_indices in enumerate(indices):
                # Filter out invalid indices (-1)
                valid_indices = voxel_indices[voxel_indices != -1]
                if len(valid_indices) > 0:
                    # Compute mean of scalar field for valid indices
                    for key in sf_keys:
                        pc_out.scalarfields[key][i] = np.mean(
                            self.scalarfields[key][valid_indices]
                        )

        if self.has_color:
            # region output (console)

            if verbose >= VerboseLevel.DEBUG:
                print(
                    f"{Fore.CYAN}[DEBUG] Processing colors -> "
                    f"Input color shape: {self.color.shape}"
                    f"{Style.RESET_ALL}\n"
                )

            # endregion output (console)

            # Initialize array for mean colors
            num_voxels = len(indices)
            pc_out.color = np.zeros((num_voxels, 3))

            # Compute mean color for each voxel
            for i, voxel_indices in enumerate(indices):
                # Filter out invalid indices (-1)
                valid_indices = voxel_indices[voxel_indices != -1]
                if len(valid_indices) > 0:
                    # Compute mean of colors for valid indices
                    pc_out.color[i] = np.mean(
                        self.color[valid_indices, :], axis=0
                    )

        # endregion averaging not supported (o3d) parameters

        return pc_out, indices

    def _subsample_voxel_random(
        self, voxel_size: float, verbose: int = VerboseLevel.SILENT
    ) -> tuple["PointCloud", np.ndarray]:
        """Subsamples the point cloud using voxel random sampling.

        Uses voxel grid filtering with random point selection within each voxel.

        Args:
            voxel_size (float):         The size of the voxel for subsampling.
            verbose    (int, optional): Verbosity level for logging. Defaults to VerboseLevel.SILENT.

        Returns:
            tuple: A tuple containing:
                - PointCloud: The subsampled point cloud.
                - np.ndarray: Indices of inlier points retained in the filtered point cloud.
        """  # noqa: E501

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG]"
                f" Voxel random subsampling details\n"
                f"  - Input points: {self.count:_}\n"
                f"  - Voxel size: {voxel_size}"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        voxel_indices = np.floor(self._xyz / voxel_size).astype(np.int32)
        _, unique_indices = np.unique(voxel_indices, axis=0, return_index=True)

        pcOut = self.select_by_index(unique_indices)

        indices = unique_indices

        return pcOut, indices

    # endregion subsample

    def merge(self, pc: "PointCloud", keepindex: bool = True) -> "PointCloud":
        """Merges two input point clouds to one point cloud object

        Args:
            pc (PointCloud): The point cloud to merge with.
            keepindex (bool, optional): Whether to keep the original indices. Defaults to True.

        Returns:
            PointCloud: The merged point cloud.
        """  # noqa: E501

        pcout = PointCloud()

        pcout.xyz = np.concatenate((self._xyz, pc._xyz))

        if keepindex:
            # Create indices
            if (
                "id" in self.scalarfields.keys()
                and "id" not in pc.scalarfields.keys()
            ):
                id_max = np.nanmax(self.scalarfields["id"])
                pcout.scalarfields["id"] = np.concatenate((
                    self.scalarfields["id"],
                    (id_max + 1) * np.ones(pc.time.shape, dtype=np.uint8),
                ))

            elif (
                "id" not in self.scalarfields.keys()
                and "id" in pc.scalarfields.keys()
            ):
                id_max = np.nanmax(pc.scalarfields["id"])
                pcout.scalarfields["id"] = np.concatenate((
                    (id_max + 1) * np.ones(self.time.shape, dtype=np.uint8),
                    self.scalarfields["id"],
                ))

            elif (
                "id" in self.scalarfields.keys()
                and "id" in pc.scalarfields.keys()
            ):
                id_max = np.nanmax(self.scalarfields["id"])
                pcout.scalarfields["id"] = np.concatenate((
                    self.scalarfields["id"],
                    pc.scalarfield["id"] + id_max,
                ))

            elif (
                "id" not in self.scalarfields.keys()
                and "id" not in pc.scalarfields.keys()
            ):
                pcout.add_scalarfield(
                    np.concatenate((
                        1 * np.ones(self.time.shape, dtype=np.uint8),
                        2 * np.ones(pc.time.shape, dtype=np.uint8),
                    )),
                    "id",
                )
                # pcout.scalarfields["id"] = np.concatenate(
                #     (
                #         1 * np.ones(self.time.shape, dtype=np.uint8),
                #         2 * np.ones(pc.time.shape, dtype=np.uint8),
                #     )
                # )

        if self.has_intensity:
            pcout.intensity = np.concatenate((self.intensity, pc.intensity))
        if self.has_time:
            pcout.time = np.concatenate((self.time, pc.time))
        if self.has_normals:
            pcout.normals = np.concatenate((self.normals, pc.normals))
        if self.has_color:
            pcout.color = np.concatenate((self.color, pc.color))

        # Merge scalarfields
        for key, _ in self.scalarfields.items():
            if key != "id":
                pcout.scalarfields[key] = np.concatenate((
                    self.scalarfields[key],
                    pc.scalarfields[key],
                ))

        return pcout

    # region Transformations

    def transform(self, T: np.ndarray) -> None:
        """Transforms the point cloud with the transformation matrix T (Translation + Rotation)

        Args:
            T (np.ndarray): The 4x4 transformation matrix to apply.
                           T[:3, :3] contains the 3x3 rotation matrix.
                           T[:3, 3] contains the translation vector [tx, ty, tz].
        """  # noqa: E501

        self._xyz = self._xyz - T[:3, 3]
        self._xyz = np.dot(self._xyz, T[:3, :3])

        # Compute bounding box and center
        self.bbox = self._get_bounding_box()
        self.txyz = self._get_center()

    def shiftxyz(self, t: np.ndarray) -> None:
        """Transforms the point cloud with the translation t

        Args:
            t (np.ndarray): The translation vector [tx, ty, tz].
        """

        self.xyz = self._xyz + t

    # endregion Transformations

    def pca(
        self, axis: str = "xyz", transform_points: bool = True
    ) -> tuple[float, PCA]:
        """Computes the PCA for point data of the point cloud with the axes specified in the variable axis

        Support axes:
            - 'xyz' (Default): 3D PCA
            - 'xy': 2D PCA of x and y coordinates of point cloud data
            - 'xz': 2D PCA of x and z coordinates of point cloud data
            - 'yz': 2D PCA of y and z coordinates of point cloud data

        Args:
            axis (str, optional): The axis to compute PCA on. Defaults to "xyz".
            transform_points (bool, optional): Whether to transform the point cloud to the PCA space.
                                               Defaults to True.

        Returns:
            tuple: A tuple containing:
                - theta: The angle of rotation (in radians)
                - pca: The fitted PCA object
        """  # noqa: E501

        if axis == "xyz":
            pca = PCA(n_components=3, svd_solver="full")
            pca.fit(self._xyz)
            theta = np.arctan2(-pca.components_[1, 0], pca.components_[0, 0])

            if transform_points:
                XYZ = pca.transform(self._xyz)
                self.xyz = XYZ

        else:
            pca = PCA(n_components=2)

            match axis:
                case "xy":
                    pca.fit(np.c_[self._xyz[:, 0], self._xyz[:, 1]])

                    theta = np.arctan2(
                        -pca.components_[1, 0], pca.components_[0, 0]
                    )
                    print("Theta (PCA):", np.rad2deg(theta))

                    if transform_points:
                        XY = pca.transform(
                            np.c_[self._xyz[:, 0], self._xyz[:, 1]]
                        )
                        self._xyz[:, 0:2] = XY

                case "xz":
                    pca.fit(np.c_[self._xyz[:, 0], self._xyz[:, 2]])

                    theta = np.arctan2(
                        -pca.components_[1, 0], pca.components_[0, 0]
                    )
                    print("Theta: (PCA)", np.rad2deg(theta))

                    if transform_points:
                        XZ = pca.transform(
                            np.c_[self._xyz[:, 0], self._xyz[:, 2]]
                        )
                        self._xyz[:, 0], self._xyz[:, 2] = XZ[:, 0], XZ[:, 1]

                case "yz":
                    pca.fit(np.c_[self._xyz[:, 1], self._xyz[:, 2]])

                    theta = np.arctan2(
                        -pca.components_[1, 0], pca.components_[0, 0]
                    )
                    print("Theta: ", np.rad2deg(theta))

                    if transform_points:
                        YZ = pca.transform(
                            np.c_[self._xyz[:, 1], self._xyz[:, 2]]
                        )
                        self._xyz[:, 1], self._xyz[:, 2] = YZ[:, 0], YZ[:, 1]

            self.bbox = self._get_bounding_box()
            self.txyz = self._get_center()

        return theta, pca

    def split(
        self,
        timestamp: float,
    ) -> tuple["PointCloud", "PointCloud", np.ndarray, np.ndarray]:
        """Splits the point cloud into two point clouds based on a timestamp

        Args:
            timestamp (float): The timestamp to split the point cloud at.

        Returns:
            tuple: A tuple containing:
                - PointCloud: The first point cloud with points before the timestamp.
                - PointCloud: The second point cloud with points after the timestamp.
                - np.ndarray: Indices of points in the first point cloud.
                - np.ndarray: Indices of points in the second point cloud.
        """  # noqa: E501

        indices1 = np.where(self.time <= timestamp)[0]
        indices2 = np.where(self.time > timestamp)[0]

        pc1 = self.select_by_index(indices1)
        pc2 = self.select_by_index(indices2)

        return pc1, pc2, indices1, indices2

    def dbscan(
        self,
        eps: float = 0.5,
        min_points: int = 5,
        verbose: int = VerboseLevel.SILENT,
    ) -> np.ndarray:
        """Apply DBSCAN clustering to the point cloud using Open3D.

        This method uses Open3D's implementation of DBSCAN.

        Args:
            eps        (float, optional): Maximum distance between two points to be considered neighbors.
                                          Defaults to 0.5.
            min_points (int,   optional): Minimum number of points required to form a dense region (cluster).
                                          Defaults to 5.
            verbose    (int,   optional): Verbosity level (0=silent, 1=error, 2=warning, 3=info, 4=debug).
                                          Defaults to VerboseLevel.SILENT.

        Returns:
            np.ndarray: Array of cluster labels for each point.
                        Points with label -1 are considered noise/outliers.
                        Cluster labels start from 0.
        """  # noqa: E501

        # region output (console)

        if verbose > VerboseLevel.SILENT:
            print(
                f"{Style.BRIGHT}{Fore.MAGENTA}"
                "┏" + "━" * 40 + "┓\n"
                f"┃{'DBSCAN Clustering':^40}┃\n"
                "┗" + "━" * 40 + "┛"
                f"{Style.RESET_ALL}\n"
            )

        if verbose >= VerboseLevel.DEBUG:
            print(
                f"{Fore.CYAN}[DEBUG] Input parameters\n"
                f"  - eps: {eps}\n"
                f"  - min_points: {min_points}\n"
                f"  - Number of points: {self.count:_}"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        # Convert to Open3D point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(self._xyz)

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(f"{Fore.CYAN}[DEBUG] Open3D cluster_dbscan:")

        # endregion output (console)

        # Perform DBSCAN clustering
        labels = np.array(
            pcd.cluster_dbscan(
                eps=eps,
                min_points=min_points,
                print_progress=(verbose >= VerboseLevel.DEBUG),
            )
        )

        # region output (console)

        if verbose >= VerboseLevel.DEBUG:
            print(f"{Style.RESET_ALL}\n")

        if verbose >= VerboseLevel.INFO:
            num_clusters = labels.max() + 1
            num_noise = np.sum(labels == -1)

        if verbose >= VerboseLevel.ERROR and num_clusters == 0:
            print(
                f"{Fore.RED}[ERROR] No clusters found! "
                f"Try increasing eps or decreasing min_points."
                f"{Style.RESET_ALL}\n"
            )

        if verbose >= VerboseLevel.WARNING and (num_noise / len(labels)) > 0.5:
            print(
                f"{Fore.YELLOW}[WARNING] More than 50% noise points! "
                f"Consider adjusting parameters."
                f"{Style.RESET_ALL}\n"
            )

        if verbose >= VerboseLevel.INFO:
            if num_clusters > 0:
                largest_cluster = np.bincount(labels[labels >= 0]).max()
            else:
                largest_cluster = 0

            noise_percent = 100 * num_noise / len(labels)

            print(
                f"{Fore.WHITE}[INFO] DBSCAN clustering completed\n"
                f"  - Number of clusters: {num_clusters}\n"
                f"  - Noise points: {num_noise:_} ({noise_percent:.2f}%)\n"
                f"  - Largest cluster: {largest_cluster:_} points"
                f"{Style.RESET_ALL}\n"
            )

        # endregion output (console)

        return labels
