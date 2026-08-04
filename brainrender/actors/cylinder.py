"""Cylinder actor for brainrender scenes."""

import numpy.typing as npt
from loguru import logger
from vedo import Mesh, shapes

from brainrender.actor import Actor


class Cylinder(Actor):
    """Actor representing a cylinder between a point and the brain's surface."""

    def __init__(
        self,
        pos: npt.ArrayLike | Mesh | Actor,
        root: Actor,
        color: str = "powderblue",
        alpha: float = 1,
        radius: float = 350,
    ) -> None:
        """
        Parameters
        ----------
        pos
            AP, DV, ML coordinates. If a Mesh or Actor is passed,
            the centre of mass is used instead.
        root
            Brain root Actor or mesh.
        color
            Colour name. Default ``"powderblue"``.
        alpha
            Transparency. Default 1.
        radius
            Cylinder radius. Default 350.
        """

        # Get pos
        if isinstance(pos, Mesh):
            pos = pos.center_of_mass()
        elif isinstance(pos, Actor):
            pos = pos.center
        logger.debug(f"Creating Cylinder actor at: {pos}")

        # Get point at top of cylinder
        top = pos.copy()
        top[1] = root.bounds()[2] - 500

        # Create mesh and Actor
        mesh = shapes.Cylinder(pos=[top, pos], c=color, r=radius, alpha=alpha)
        Actor.__init__(self, mesh, name="Cylinder", br_class="Cylinder")
