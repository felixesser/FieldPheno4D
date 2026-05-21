import click
import numpy as np

from PointCloudLib.python.least_squares_adjustments.PlaneAdjustment import \
    PlaneAdjustment
from PointCloudLib.python.pointcloudlibcore.pointcloudlibcore import pointcloud


@click.command()
@click.option("--path_data", "-p", default="../../tmp/pointclouds/", type=str, help="Path to the data directory")
@click.option("--point_cloud_file", "-p", default="xyz_zf.txt", type=str, help="Name of the point cloud file")

def main(path_data,
         point_cloud_file):

    # Read pointcloud from file
    pc = pointcloud()
    pc.read(path_data + point_cloud_file)

    # Create object and read data
    offset = np.min(pc.xyz,axis=0)
    pc.shiftxyz(-offset)
    PlaneLSA = PlaneAdjustment( pc=pc )
    PlaneLSA.run()
    pc.shiftxyz(offset)
    #PlaneLSA.compute_point_to_plane_distances()
    PlaneLSA.print_results()

    PlaneLSA.visualize_results()




if __name__ == "__main__":
    main()