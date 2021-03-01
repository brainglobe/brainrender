import numpy as np
from vedo import Spheres, Sphere
from vedo import Points as vPoints
from pathlib import Path
from pyinspect.utils import _class_name
from loguru import logger


from brainrender.actor import Actor


class Point(Actor):
    def __init__(
        self, pos, radius=100, color="blackboard", alpha=1, res=25, name=None
    ):
        """
        Creates an actor representing a single point
        :param pos: list or np.ndarray with coordinates
        :param radius: float
        :param color: str,
        :param alpha: float
        :param res: int, resolution of mesh
        :param name: str, actor name
        """
        logger.debug(f"Creating a point actor at: {pos}")
        mesh = Sphere(pos=pos, r=radius, c=color, alpha=alpha, res=res)
        name = name or "Point"
        Actor.__init__(self, mesh, name=name, br_class="Point")


class PointsBase:
    def __init__(
        self,
    ):
        """
        Base class with functinality to load from file.
        """
        return

    def _from_numpy(self, data):
        """
        Creates the mesh
        """
        N = len(data)
        if not isinstance(self.colors, str):
            if not N == len(self.colors):  # pragma: no cover
                raise ValueError(  # pragma: no cover
                    "When passing a list of colors, the number of colors shou  # pragma: no coverld match the number of cells"  # pragma: no cover
                )  # pragma: no cover

        self.name = self.name or "Points"
        mesh = Spheres(
            data, r=self.radius, c=self.colors, alpha=self.alpha, res=self.res
        )
        return mesh

    def _from_file(self, data, colors="salmon", alpha=1):
        """
        Loads points coordinates from a numpy file
        before creating the mesh.
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
    def __init__(self, data, name=None, colors="salmon", alpha=1, radius=20, res=8):
        """
        Creates an actor representing multiple points (more efficient than
        creating many Point instances).

        :param data: np.ndarray, Nx3 array or path to .npy file with coords data
        :param radius: float
        :param color: str, or list of str with color names or hex codes
        :param alpha: float
        :param name: str, actor name
        :param res: int. Resolution of sphere actors
        """
        PointsBase.__init__(self)
        logger.debug(f"Creating a Points actor")

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
    def __init__(
        self, data, name=None, dims=(40, 40, 40), radius=None, **kwargs
    ):
        """
        Creates a Volume actor showing the 3d density of a set
        of points.

        :param data: np.ndarray, Nx3 array with cell coordinates


        from vedo:
            Generate a density field from a point cloud. Input can also be a set of 3D coordinates.
            Output is a ``Volume``.
            The local neighborhood is specified as the `radius` around each sample position (each voxel).
            The density is expressed as the number of counts in the radius search.

            :param int,list dims: numer of voxels in x, y and z of the output Volume.

        """
        logger.debug(f"Creating a PointsDensity actor")
        volume = vPoints(data).density(
            dims=dims, radius=radius, **kwargs
        )  # returns a vedo Volume
        Actor.__init__(self, volume, name=name, br_class="density")
