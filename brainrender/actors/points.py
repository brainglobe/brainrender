"""Point and point-cloud actors for brainrender scenes."""

from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from loguru import logger
from pyinspect.utils import _class_name
from vedo import Mesh, Sphere, Spheres
from vedo import Points as vPoints

from brainrender.actor import Actor


class Point(Actor):
    """Actor representing a single point as a sphere."""

    def __init__(
        self,
        pos: npt.ArrayLike,
        radius: float = 100,
        color: str = "blackboard",
        alpha: float = 1,
        res: int = 25,
        name: str | None = None,
    ) -> None:
        """
        Parameters
        ----------
        pos
            Coordinates of the point.
        radius
            Sphere radius. Default 100.
        color
            Colour name. Default ``"blackboard"``.
        alpha
            Transparency. Default 1.
        res
            Mesh resolution. Default 25.
        name
            Actor name. Default ``"Point"``.
        """
        logger.debug(f"Creating a point actor at: {pos}")
        mesh = Sphere(pos=pos, r=radius, c=color, alpha=alpha, res=res)
        name = name or "Point"
        Actor.__init__(self, mesh, name=name, br_class="Point")


class PointsBase:
    """Base class with shared file-loading functionality for point actors."""

    def __init__(self) -> None:
        return

    def _from_numpy(self, data: npt.NDArray) -> Mesh:
        """
        Create a Spheres mesh from a numpy array.

        Parameters
        ----------
        data
            Nx3 array of point coordinates.

        Returns
        -------
        vedo.Mesh

        Raises
        ------
        ValueError
            If the number of colours does not match the number of points.
        """
        N = len(data)
        if not isinstance(self.colors, str):
            if not N == len(self.colors):  # pragma: no cover
                raise ValueError(  # pragma: no cover
                    "When passing a list of colors, the number of colors should match the number of cells"  # pragma: no cover
                )  # pragma: no cover

        self.name = self.name or "Points"
        mesh = Spheres(
            data, r=self.radius, c=self.colors, alpha=self.alpha, res=self.res
        )
        return mesh

    def _from_file(
        self,
        data: str | Path,
        colors: str = "salmon",
        alpha: float = 1,
    ) -> Mesh:
        """
        Load point coordinates from a ``.npy`` file and create the mesh.

        Parameters
        ----------
        data
            Path to the ``.npy`` file.
        colors
            Colour name. Default ``"salmon"``.
        alpha
            Transparency. Default 1.

        Returns
        -------
        vedo.Mesh

        Raises
        ------
        FileExistsError
            If the file does not exist.
        NotImplementedError
            If the file format is not ``.npy``.
        """
        path = Path(data)
        if not path.exists():
            raise FileExistsError(f"File {data} does not exist")

        if path.suffix == ".npy":
            self.name = self.name or path.name
            return self._from_numpy(
                np.load(path),
            )
        else:  # pragma: no cover
            raise NotImplementedError(  # pragma: no cover
                f"Add points from file only works with numpy file for now, not {path.suffix}."  # pragma: no cover
                + "If youd like more formats supported open an issue on Github!"  # pragma: no cover
            )  # pragma: no cover


class Points(PointsBase, Actor):
    """
    Actor representing multiple points as spheres.
    """

    def __init__(
        self,
        data: npt.NDArray | str | Path,
        name: str | None = None,
        colors: str | list[str] = "salmon",
        alpha: float = 1,
        radius: float = 20,
        res: int = 8,
    ) -> None:
        """
        Parameters
        ----------
        data
            Nx3 array of coordinates, or path to a ``.npy`` file.
        name
            Actor name.
        colors
            Colour name or list of colour names/hex codes.
        alpha
            Transparency. Default 1.
        radius
            Sphere radius. Default 20.
        res
            Sphere mesh resolution. Default 8.

        Raises
        ------
        TypeError
            If ``data`` is not a numpy array or file path.
        """
        PointsBase.__init__(self)
        logger.debug("Creating a Points actor")

        self.radius = radius
        self.colors = colors
        self.alpha = alpha
        self.name = name
        self.res = res

        if isinstance(data, np.ndarray):
            mesh = self._from_numpy(data)
        elif isinstance(data, (str, Path)):
            mesh = self._from_file(data)
        else:  # pragma: no cover
            raise TypeError(  # pragma: no cover
                f"Input data should be either a numpy array or a file path, not: {_class_name(data)}"  # pragma: no cover
            )  # pragma: no cover

        Actor.__init__(self, mesh, name=self.name, br_class="Points")


class PointsDensity(Actor):
    """Actor showing the 3D density of a point cloud as a volume."""

    def __init__(
        self,
        data: npt.NDArray,
        name: str | None = None,
        dims: tuple[int, int, int] = (40, 40, 40),
        radius: float | None = None,
        colors: str = "Dark2",
        **kwargs: Any,
    ) -> None:
        """
        Parameters
        ----------
        data
            Nx3 array of point coordinates.
        name
            Actor name.
        dims
            Number of voxels in x, y, z of the output Volume. Default ``(40, 40, 40)``.
        radius
            Neighbourhood radius for density estimation. If None, vedo infers it.
        colors
            Matplotlib colormap name. Default ``"Dark2"``.
        **kwargs
            Additional keyword arguments forwarded to vedo's ``density``.
        """
        logger.debug("Creating a PointsDensity actor")

        # flip coordinates on XY axis to match brainrender coordinates system
        data[:, 2] = -data[:, 2]

        # create volume and then actor
        volume = (
            vPoints(data)
            .density(dims=dims, radius=radius, **kwargs)
            .cmap(colors)
            .alpha([0, 0.9])
            .mode(1)
        )  # returns a vedo Volume

        Actor.__init__(self, volume, name=name, br_class="density")
