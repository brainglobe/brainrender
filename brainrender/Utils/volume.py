"""
    Code useful for dealing with volumetric data (e.g. allen annotation volume for the mouse atlas)
"""
from vtkplotter import Volume
import numpy as np
from brainrender.Utils.data_io import load_volume_file


def load_labelled_volume(data, vmin=0, alpha=1, **kwargs):
    """
        Load volume image from .nrrd file. 
        It assume that voxels with value = 0 are empty while voxels with values > 0
        are labelles (e.g. to indicate the location of a brain region in a reference atlas)

        :param data: str, path to file with volume data or 3d numpy array
        :param vmin: float, values below this numner will be assigned an alpha=0 and not be visualized
        :param **kwargs: kwargs to pass to the Volume class from vtkplotter
        :param alpha: float in range [0, 1], transparency [for the part of volume with value > vmin]
    """
    # Load/check volumetric data
    if isinstance(data, str):  # load from file
        data = load_volume_file(data)
    elif not isinstance(data, np.ndarray):
        raise ValueError(
            f"Data should be a filepath or np array, not: {data.__type__}"
        )

    # Create volume and set transparency range
    vol = Volume(data, alpha=alpha, **kwargs)

    otf = vol.GetProperty().GetScalarOpacity()
    otf.RemoveAllPoints()
    otf.AddPoint(vmin, 0)  # set to transparent
    otf.AddPoint(vmin + 0.1, alpha)  # set to opaque
    otf.AddPoint(data.max(), alpha)

    return vol


def extract_volume_surface(vol, threshold=0.1, smooth=False):
    """ 
        Returns a vtkplotter mesh actor with just the outer surface of a volume

        :param vol: instance of Volume class from vtkplotter
        :param threshold: float, min value to threshold the volume for isosurface extraction
        :param smooth: bool, if True the surface mesh is smoothed
    """

    if not isinstance(vol, Volume):
        raise TypeError(
            f"vol argument should be an instance of Volume not {vol.__type__}"
        )

    mesh = vol.isosurface(threshold=threshold).cap()

    if smooth:
        mesh.smoothLaplacian()

    return mesh


def extract_label_mesh(vol, lbl):
    """
        Given a vtkplotter Volume with a scalar value labelling each voxel, 
        this function returns a mesh of only the voxels whose value matches the lbl argument

        :param vol: a vtkplotter Volume
        :param lbl: float or int
    """
    if not isinstance(vol, Volume):
        raise TypeError(
            f"vol argument should be an instance of Volume not {vol.__type__}"
        )

    mask = vol.threshold(above=lbl - 0.1, below=lbl + 0.1)
    return extract_volume_surface(mask, threshold=lbl - 0.1)
