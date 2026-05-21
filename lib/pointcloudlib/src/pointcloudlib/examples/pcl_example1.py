import numpy as np

from pointcloudlib import PointCloud
from pointcloudlib.segmentation import clothsimulationfilter


def main():

    # Path to dataset and name
    datasetinfo = ["P147/230621/LMI/pointclouds", "Sugar Corn"]

    # Point cloud files
    pclfiles = ['kinematiccalibration/PCL.las', 'kinematiccalibration/PCR.las']
    m3c2files = ['kinematiccalibration/PCL_m3c2.txt', 'kinematiccalibration/PCR_m3c2.txt']
    
    # ______________________________________________________________________________________________________
    # 1) Read data
    
    # Read point clouds
    pcl, pcr = PointCloud(), PointCloud()
    pcl.read( fname = "../tmp/data/Phenobot/FieldPheno4D/" + datasetinfo[0] + "/" + pclfiles[0], verbose=1 )
    pcr.read( fname = "../tmp/data/Phenobot/FieldPheno4D/" + datasetinfo[0] + "/" + pclfiles[1], verbose=1 )

    # ______________________________________________________________________________________________________
    # 3) Subsampling for visualization

    # Random subsampling
    pcl, _ = pcl.subsample( factor = 100, method = "random")
    pcr, _ = pcr.subsample( factor = 100, method = "random")

    # ______________________________________________________________________________________________________
    # 4) Merge two point clouds

    pc = pcl.merge( pcr )

    pc.add_scalarfield(X=pc.xyz[:,2], name="height")

    # ______________________________________________________________________________________________________
    # 5) Transform point clouds to local

    # Rotate points using PCA
    _ = pc.pca( axis="xy", transform_points=True )
    _ = pc.pca( axis="xz", transform_points=True )

    # Z translation
    pc.shiftxyz( t = np.array([np.min(pc.xyz[:,0]), np.min(pc.xyz[:,1]), np.min(pc.xyz[:,2])]) )

    # ______________________________________________________________________________________________________
    # 6) Segmentation of the pointcloud by ground and non-ground points

    # Cloth Simulation Filter (CSF)
    idx = clothsimulationfilter( pc, verbose=1 )

    # Add new scalarfield
    pc.add_scalarfield( X = idx, name="class_id" )

    # ______________________________________________________________________________________________________
    # 8) Compute Digital Elevation Model (DEM) with the points

    pc.plot( scalarfield="height") # height
    pc.plot( scalarfield="class_id") # class_id

    # ______________________________________________________________________________________________________
    # 9) Compute Digital Elevation Model (DEM) with the points

    # Compute Digital Elevation Model
    pc.compute_dem( xylimits=pc.bbox, dxy=0.02, vis=True )
    
    # ______________________________________________________________________________________________________
    # 7) Write to file

    pc.write( fname="tmp/pctest.las")

    
    


if __name__ == "__main__":
    main()