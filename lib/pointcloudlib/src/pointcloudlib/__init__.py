"""init file for pointcloudlib package.
Attaches methods to PointCloud class.
"""

import inspect
from pointcloudlib.pointcloud import PointCloud
from pointcloudlib.visualization import Visualization
from pointcloudlib.cleaning import Cleaning
from pointcloudlib.registration.icp.icp import ICP
from pointcloudlib.dem import process_plot_dem


def attach_instance_methods(source_class, target_class):
    """Attach all instance methods from source_class to target_class.

    Excludes:
        - Static methods (without 'self' parameter)
        - Class methods

    Args:
        source_class: Class containing methods to attach
        target_class: Class to attach methods to
    """
    for name, method in inspect.getmembers(source_class, inspect.isfunction):

        # Check if method has 'self' as first parameter (instance method)
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())

        # Only attach if first parameter is 'self'
        if params and params[0] == "self":
            setattr(target_class, name, method)


# Attach all methods from Visualization to PointCloud
attach_instance_methods(Visualization, PointCloud)

# Attach all methods from Cleaning to PointCloud
attach_instance_methods(Cleaning, PointCloud)

# Attach all methods from ICP to PointCloud
attach_instance_methods(ICP, PointCloud)
