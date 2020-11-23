from vedo import Volume as VedoVolume
import numpy as np

from brainrender.actor import Actor


class Volume(Actor):
    def __init__(
        self,
        griddata,
        voxel_size=1,
        cmap="bwr",
        min_quantile=None,
        min_value=None,
        name=None,
        br_class=None,
    ):
        """
            Takes a 3d numpy array with volumetric data
            and returns an Actor with mesh: vedo.Volume.isosurface.
            The isosurface needs a lower bound threshold, this can be
            either a user defined hard value (min_value) or the value
            corresponding to some percentile of the grid data.

            :param griddata: np.ndarray, 3d array with grid data
            :param voxel_size: int, size of each voxel in microns
            :param min_quantile: float, percentile for threshold
            :param min_value: float, value for threshold
            :param cmap: str, name of colormap to use
        """
        # Get threshold
        if min_quantile is None and min_value is None:
            th = 0
        elif min_value is not None:
            th = min_value
        else:
            th = np.percentile(griddata.ravel(), min_quantile)

        # Create mesh
        mesh = VedoVolume(
            griddata, spacing=[voxel_size, voxel_size, voxel_size],
        )
        mesh = mesh.legosurface(vmin=th, cmap=cmap)

        Actor.__init__(
            self, mesh, name=name or "Volume", br_class=br_class or "Volume"
        )
