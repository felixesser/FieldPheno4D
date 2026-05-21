import numpy as np

from pointcloudlib import PointCloud


def main():
    
    # ______________________________________________________________________________________________________
    # 1) Read data
    
    # Read point clouds
    pcL, pcR = PointCloud(), PointCloud()
    pcL.read( fname = "../../tmp/data/Phenobot/FieldPheno4D/P147/230621/LMI/pointclouds/singleplants/sugarcorn/PCL.las", verbose=1 )
    pcR.read( fname = "../../tmp/data/Phenobot/FieldPheno4D/P147/230621/LMI/pointclouds/singleplants/sugarcorn/PCR.las", verbose=1 )



    pc = pcL.merge(pcR)
    
    pc.shiftxyz(t=np.array([0,0,-pc.xyz[:,2].min()]))

    # Add height 
    pc.add_scalarfield( X=pc.xyz[:,2], name="height" )

    # Create .gif visualization
    pc.cloud_2_gif(
        sc_field="height",
        cmap="viridis",  # bwr: id, viridis: height
        fname="../../tmp/data/Phenobot/FieldPheno4D/P147/230621/LMI/pointclouds/singleplants/sugarcorn/height.gif",
    )

if __name__ == "__main__":
    main()