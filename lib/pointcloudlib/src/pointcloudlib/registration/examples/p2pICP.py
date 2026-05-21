import click
import numpy as np
from pointcloudlib.registration.icp.p2pICP import SymPlane2PlaneICP
from pointcloudlib.registration.icp.p2pICP_config import p2pICPconfig

from pointcloudlib import PointCloud


@click.command()
@click.option(
    "--path_data",
    "-p",
    default="../../data/pointclouds/",
    type=str,
    help="Path to the data directory",
)
def main(path_data):

    # ______________________________________________________________________________________________________
    # 1) Read data

    # Read point clouds
    pcl, pcr = PointCloud(), PointCloud()
    pcl.read(fname=path_data + "bean_l.las", verbose=1)
    pcr.read(fname=path_data + "bean_r.las", verbose=1)

    # Read ICP configfile
    ICPconfig = p2pICPconfig()
    ICPconfig.readfromjson("config/p2pICPconfig.json")

    # Shift point cloud by center of first point cloud
    txyz = pcl.txyz.copy()
    pcr.shiftxyz(-txyz)
    pcl.shiftxyz(-txyz)

    pc = pcl.merge(pcr)
    # pc.plot( scalarfield="id" )

    # ______________________________________________________________________________________________________
    # 2) Run symmetric plane-to-plane ICP

    icp_instance = SymPlane2PlaneICP(pcl, pcr, x=np.zeros(6))
    x, pcl_r, pcr_r = icp_instance.runICP(config=ICPconfig, symmetric=False)

    # Merge the two point clouds
    pc_r = pcl_r.merge(pcr_r)
    # pc_r.plot( scalarfield="id" )

    # Shift to global frame
    # pc_r.shiftxyz( txyz )

    pc_r.add_scalarfield(X=pc_r.xyz[:, 2], name="height")

    # Write registered point clouds to folder
    pc_r.write(fname=path_data + "sugarcorn_reg.las")


if __name__ == "__main__":
    main()
