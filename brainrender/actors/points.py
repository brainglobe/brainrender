import numpy as np
from vedo import Spheres, Sphere
from pathlib import Path
from pyinspect.utils import _class_name

from ..actor import Actor


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
        mesh = Sphere(pos=pos, r=radius, c=color, alpha=alpha, res=res)
        name = name or "Point"
        Actor.__init__(self, mesh, name=name, br_class="Point")


class Points(Actor):
    def __init__(self, data, name=None, colors="salmon", alpha=1, radius=20):
        """
            Creates an actor representing multiple points (more efficient than 
            creating many Point instances).

            :param data: np.ndarray, Nx3 array or path to .npy file with coords data
            :param radius: float
            :param color: str,
            :param alpha: float
            :param name: str, actor name
        """
        self.radius = radius
        self.colors = colors
        self.alpha = alpha
        self.name = name

        if isinstance(data, np.ndarray):
            mesh = self._from_numpy(data)
        elif isinstance(data, (str, Path)):
            mesh = self._from_file(data)
        else:
            raise TypeError(
                f"Input data should be either a numpy array or a file path, not: {_class_name(data)}"
            )

        Actor.__init__(self, mesh, name=self.name, br_class="Points")

    def _from_numpy(self, data):
        """
            Creates the mesh
        """
        N = len(data)
        if not isinstance(self.colors, str):
            if not N == len(self.colors):
                raise ValueError(
                    "When passing a list of colors, the number of colors should match the number of cells"
                )

        self.name = self.name or "Points"
        mesh = Spheres(
            data, r=self.radius, c=self.colors, alpha=self.alpha, res=8
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
            return self._from_numpy(np.load(path),)
        else:
            raise NotImplementedError(
                f"Add points from file only works with numpy file for now, now {path.suffix}."
                + "If youd like more formats supported open an issue on Github!"
            )
