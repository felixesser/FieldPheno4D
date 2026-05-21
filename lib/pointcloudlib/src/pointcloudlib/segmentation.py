import CSF
import numpy as np
from colorama import Fore, Style

from pointcloudlib import PointCloud


def clothsimulationfilter(pc: PointCloud, verbose=0) -> np.ndarray:

    csf = CSF.CSF()
    csf.params.bSloopSmooth = True
    csf.params.cloth_resolution = 1
    csf.params.rigidness = 3
    csf.params.time_step = 0.65
    csf.params.class_threshold = 0.08
    csf.params.interations = 500

    # Terminal print
    if verbose == 1:
        print(
            (
                " ____________________________________________________________________________\n"
                "| \n"
                f"| {Style.BRIGHT}{Fore.MAGENTA}{'Clothsimulation Filter'}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- Number of points:      '+str(len(pc.xyz[:,0]))}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- bSloopSmooth:  ' + str(csf.params.bSloopSmooth)}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- cloth_resolution:  ' + str(csf.params.cloth_resolution)}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- rigidness:  ' + str(csf.params.rigidness)}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- time_step:  ' + str(csf.params.time_step)}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- class_threshold:  ' + str(csf.params.class_threshold)}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- cloth_resolution:  ' + str(csf.params.cloth_resolution)}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- iterations:  ' + str(csf.params.interations)}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'  running ... '}{Style.RESET_ALL}"
            )
        )

    csf.setPointCloud(pc.xyz)
    ground = (
        CSF.VecInt()
    )  # a list to indicate the index of ground points after calculation
    non_ground = (
        CSF.VecInt()
    )  # a list to indicate the index of non-ground points after calculation
    csf.do_filtering(ground, non_ground)  # do actual filtering.

    idx_ground = np.array(ground)
    idx_nonground = np.array(non_ground)

    idx = np.zeros(pc.xyz.shape[0])

    idx[idx_ground] = 1
    idx[idx_nonground] = 2

    # Terminal print
    if verbose == 1:
        print(
            (
                f"| {Style.BRIGHT}{Fore.WHITE}{'- Number of ground points:      '+str(len(idx_ground))}{Style.RESET_ALL}\n"
                f"| {Style.BRIGHT}{Fore.WHITE}{'- Number of non-ground points:     '+str(len(idx_nonground))}{Style.RESET_ALL}\n"
                "|____________________________________________________________________________\n"
            )
        )

    return idx
