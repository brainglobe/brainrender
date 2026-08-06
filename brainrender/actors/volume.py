"""Volume actor for rendering 3D numpy arrays as surfaces or volumes."""

from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from loguru import logger
from vedo import Volume as VedoVolume

from brainrender.actor import Actor


class Volume(Actor):
    """
    Render a 3D numpy array as a surface mesh or vedo Volume.
    By default the volume is represented as an isosurface.
    """

    def __init__(
        self,
        griddata: npt.NDArray | VedoVolume | str | Path,
        voxel_size: int = 1,
        cmap: str = "bwr",
        min_quantile: float | None = None,
        min_value: float | None = None,
        name: str | None = None,
        br_class: str | None = None,
        as_surface: bool = True,
        **volume_kwargs: Any,
    ) -> None:
        """
        Parameters
        ----------
        griddata
            3D array with grid data. Can also be a vedo Volume or a path
            to a ``.npy`` file.
        voxel_size
            Size of each voxel in microns. Default 1.
        cmap
            Colormap name. Default ``"bwr"``.
        min_quantile
            Percentile threshold for isosurface extraction.
        min_value
            Hard value threshold for isosurface extraction.
        name
            Actor name. Default ``"Volume"``.
        br_class
            Brainrender class type. Default ``"Volume"``.
        as_surface
            If True, return an isosurface mesh instead of the full volume.
            Default True.
        **volume_kwargs
            Keyword arguments forwarded to vedo's Volume class.
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

    def _from_numpy(
        self,
        griddata: npt.NDArray,
        voxel_size: int,
        color: str,
        **volume_kwargs: Any,
    ) -> VedoVolume:
        """
        Create a vedo Volume from a 3D numpy array.

        Parameters
        ----------
        griddata
            3D array with volume data.
        voxel_size
            Size of each voxel in microns.
        color
            Colormap name to apply.
        **volume_kwargs
            Keyword arguments forwarded to vedo's Volume class.

        Returns
        -------
        VedoVolume
            A vedo volume created from the input 3D array.
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

    def _from_file(
        self,
        filepath: str | Path,
        voxel_size: int,
        color: str,
        **volume_kwargs: Any,
    ) -> VedoVolume:
        """
        Load a ``.npy`` file and return a vedo Volume.

        Parameters
        ----------
        filepath
            Path to the ``.npy`` file.
        voxel_size
            Size of each voxel in microns.
        color
            Colormap name to apply.
        **volume_kwargs
            Keyword arguments forwarded to vedo's Volume class.

        Returns
        -------
        VedoVolume

        Raises
        ------
        FileExistsError
            If the file does not exist.
        ValueError
            If the file is not a ``.npy`` file.
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
