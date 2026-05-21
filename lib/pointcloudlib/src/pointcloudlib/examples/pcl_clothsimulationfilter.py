from pointcloudlib import PointCloud
from pointcloudlib.segmentation import clothsimulationfilter


def main():

    # 1) Create point cloud object
    pcl = PointCloud()
    pcr = PointCloud()

    # 2) Read pointcloud from folder
    pcl.read(
        fname="/mnt/d/phenobot-data/FieldPheno4D/P147/01_UGV/230621/01_LMI/02_pointclouds/02_kinematic_calibration/PCL.las",
        verbose=1,
    )
    pcr.read(
        fname="/mnt/d/phenobot-data/FieldPheno4D/P147/01_UGV/230621/01_LMI/02_pointclouds/02_kinematic_calibration/PCR.las",
        verbose=1,
    )

    # 3) Merge point clouds
    pc = pcl.merge(pcr)

    # 4) Subsampling
    pc, _ = pc.subsample(factor=1000, method="random", verbose=1)

    # 5) Compute PCAs and transform points
    pc.pca(axis="xy", transform_points=True)
    pc.pca(axis="xz", transform_points=True)

    # 6) Cloth simulation filter
    idx = clothsimulationfilter(pc)

    # Add height scalarfield to point cloud
    pc.add_scalarfield(X=idx, name="class_id")

    # 7) Visualize point cloud
    pc.plot(scalarfield="class_id")


if __name__ == "__main__":
    main()
