"""Line actor for brainrender scenes."""

import numpy.typing as npt
from vedo import shapes

from brainrender.actor import Actor


class Line(Actor):
    """Actor representing a line through a sequence of coordinates."""

    def __init__(
        self,
        coordinates: npt.ArrayLike,
        color: str | tuple = "black",
        alpha: float = 1,
        linewidth: float = 2,
        name: str | None = None,
    ) -> None:
        """
        Parameters
        ----------
        coordinates
            Array of shape (N, 3) with AP, DV, ML coordinates.
        color
            CSS colour name, hex code, or RGB tuple. Default ``"black"``.
        alpha
            Transparency in range [0, 1]. Default 1.
        linewidth
            Line width. Default 2.
        name
            Actor name.
        """
        mesh = shapes.Line(p0=coordinates, lw=linewidth, c=color, alpha=alpha)
        Actor.__init__(self, mesh, name=name, br_class="Line")
