from pathlib import Path

import numpy as np
from loguru import logger
from vedo import Volume as VedoVolume

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
        as_surface=True,
        **volume_kwargs,
    ):
        """
        Takes a 3d numpy array with volumetric data
        and returns an Actor with mesh: vedo.Volume.isosurface or a vedo.Volume.
        BY default the volume is represented as a surface

        To extract the surface:
            The isosurface needs a lower bound threshold, this can be
            either a user defined hard value (min_value) or the value
            corresponding to some percentile of the grid data.

        :param griddata: np.ndarray, 3d array with grid data. Can also be a vedo Volume
            or a file path pointing to a .npy file
        :param griddata: np.ndarray, 3d array with grid data
        :param voxel_size: int, size of each voxel in microns
        :param min_quantile: float, percentile for threshold
        :param min_value: float, value for threshold
        :param cmap: str, name of colormap to use
        :param as_surface, bool. default True. If True
            a surface mesh is returned instead of the whole volume
        :param volume_kwargs: keyword arguments for vedo's Volume class
        """
        logger.debug("Creating a Volume actor")
        # Create mesh
        color = volume_kwargs.pop("c", "viridis")
        if isinstance(griddata, np.ndarray):
            # create volume from data
            mesh = self._from_numpy(
                griddata, voxel_size, color, **volume_kwargs
            )
        elif isinstance(griddata, (str, Path)):
            # create from .npy file
            mesh = self._from_file(
                griddata, voxel_size, color, **volume_kwargs
            )
        else:
            mesh = griddata  # assume a vedo Volume was passed

        if as_surface:
            # Get threshold
            if min_quantile is None and min_value is None:
                th = 0
            elif min_value is not None:
                th = min_value
            else:
                th = np.percentile(griddata.ravel(), min_quantile)

            mesh = mesh.legosurface(vmin=th)
            mesh.cmap(cmap)

        Actor.__init__(
            self, mesh, name=name or "Volume", br_class=br_class or "Volume"
        )

    def _from_numpy(self, griddata, voxel_size, color, **volume_kwargs):
        """
        Creates a vedo.Volume actor from a 3D numpy array with volume data.
        """
        vvol = VedoVolume(
            griddata,
            spacing=[voxel_size, voxel_size, voxel_size],
            **volume_kwargs,
        )
        vvol.cmap(color)
        # The transformation below is ALREADY applied
        # to vedo.Volume instances in render.py
        # so we should not apply it here.
        # Flip volume so that it's oriented as in the atlas
        # vvol.permute_axes(2, 1, 0)
        # mtx = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]
        # vvol.apply_transform(mtx)
        return vvol

    def _from_file(self, filepath, voxel_size, color, **volume_kwargs):
        """
        Loads a .npy file and returns a vedo Volume actor.
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileExistsError(
                f"Loading volume from file, file not found: {filepath}"
            )
        if not filepath.suffix == ".npy":
            raise ValueError(
                "Loading volume from file only accepts .npy files"
            )

        return self._from_numpy(
            np.load(str(filepath)), voxel_size, color, **volume_kwargs
        )
