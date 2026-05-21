import numpy as np

from pointcloudlib import PointCloud


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
    
    # Read M3C2 distances
    d_l = np.loadtxt( fname="../tmp/data/Phenobot/FieldPheno4D/" + datasetinfo[0] + "/" +  m3c2files[0], comments="#", delimiter="," )
    d_r = np.loadtxt( fname="../tmp/data/Phenobot/FieldPheno4D/" + datasetinfo[0] + "/" +  m3c2files[1], comments="#", delimiter="," )

    # Add scalar field to point cloud object
    pcl.add_scalarfield( X = d_l, name="M3C2distance" )
    pcr.add_scalarfield( X = d_r, name="M3C2distance" )

    # ______________________________________________________________________________________________________
    # 2) Filter Nan values

    # Get indices of non-nan values
    non_nan_dl, non_nan_dr = ~np.isnan(pcl.scalarfields['M3C2distance']), ~np.isnan(pcr.scalarfields['M3C2distance'])

    pcl = pcl.select_by_index( np.where(non_nan_dl == True)[0] )
    pcr = pcr.select_by_index( np.where(non_nan_dr == True)[0] )

    # ______________________________________________________________________________________________________
    # 3) Subsampling for visualization

    # Random subsampling
    pcl, _ = pcl.subsample( factor = 100, method = "random")
    pcr, _ = pcr.subsample( factor = 100, method = "random")

    # ______________________________________________________________________________________________________
    # 4) Merge two point clouds

    pc = pcl.merge( pcr )

    # ______________________________________________________________________________________________________
    # 5) Transform point clouds to local

    # Rotate points using PCA
    _ = pc.pca( axis="xy", transform_points=True )
    _ = pc.pca( axis="xz", transform_points=True )

    # Z translation
    pc.shiftxyz( t = np.array([np.min(pc.xyz[:,0]), np.min(pc.xyz[:,1]), np.min(pc.xyz[:,2])]) )
    
    # ______________________________________________________________________________________________________
    # 6) Visualize
    
    pc.plot( scalarfield="M3C2distance" )



    
if __name__ == "__main__":
    main()