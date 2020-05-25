import pandas as pd
import numpy as np
import os
from vtkplotter import Plane

from brainrender.Utils.paths_manager import Paths

from brainrender.Utils.data_io import load_mesh_from_file
from brainrender.Utils import actors_funcs


class BGBrainRenderAtlas():
    """
    This class is the base structure for an Atlas class. Atlas-specific class will need to
    inherit from this class and re-define crucial methods to support scene creation.
    """

    # These variables are generally useful but need to be specified for each atlas
    _root_midpoint = [None, None,
                      None]  # 3d coordinates of the CoM of root mesh
    _planes_norms = dict(  # normals of planes cutting through the scene along
        # orthogonal axes. These values must be replaced if atlases
        # are oriented differently.
        sagittal=[0, 0, 1],
        coronal=[1, 0, 0],
        horizontal=[0, 1, 0],
    )
    _root_bounds = [[],
                    # size of bounding boox around atlas' root along each direction
                    [],
                    []]

    default_camera = None  # Replace this with a camera params dict to specify a default camera for your atlas

    def __init__(self, *args, **kwargs):
        """"""
        super().__init__(*args, **kwargs)

        self._root_bounds = [s // 2 for s in self.shape]
        self._root_midpoint = [s // 2 for s in self.shape]

        self.output_screenshots = None
