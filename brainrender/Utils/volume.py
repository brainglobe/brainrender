"""
    Code useful for dealing with volumetric data (e.g. allen annotation volume for the mouse atlas)
"""
from vedo import Volume


def extract_volume_surface(vol, threshold=0.1, smooth=False):
    """ 
        Returns a vedo mesh actor with just the outer surface of a volume

        :param vol: instance of Volume class from vedo
        :param threshold: float, min value to threshold the volume for isosurface extraction
        :param smooth: bool, if True the surface mesh is smoothed
    """

    if not isinstance(vol, Volume):
        raise TypeError(
            f"vol argument should be an instance of Volume not {type(vol)}"
        )

    mesh = vol.isosurface(threshold=threshold).cap()

    if smooth:
        mesh.smoothLaplacian()

    return mesh


def extract_label_mesh(vol, lbl):
    """
        Given a vedo Volume with a scalar value labelling each voxel, 
        this function returns a mesh of only the voxels whose value matches the lbl argument

        :param vol: a vedo Volume
        :param lbl: float or int
    """
    if not isinstance(vol, Volume):
        raise TypeError(
            f"vol argument should be an instance of Volume not {vol.__type__}"
        )

    mask = vol.threshold(above=lbl - 0.1, below=lbl + 0.1)
    return extract_volume_surface(mask, threshold=lbl - 0.1)
