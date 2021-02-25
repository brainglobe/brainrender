from vedo import shapes
from vedo import Mesh
from loguru import logger

from brainrender.actor import Actor


class Cylinder(Actor):
    def __init__(self, pos, root, color="powderblue", alpha=1, radius=350):
        """
        Cylinder class creates a cylinder mesh between a given
        point and the brain's surface.

        :param pos: list, np.array of ap, dv, ml coordinates.
            If an actor is passed, get's the center of mass instead
        :param root: brain root Actor or mesh object
        :param color: str, color
        :param alpha: float
        :param radius: float
        """
        logger.info(f"Creating Cylinder actor at: {pos}")
        # Get pos
        if isinstance(pos, (Actor, Mesh)):
            pos = pos.centerOfMass()

        # Get point at top of cylinder
        top = pos.copy()
        top[1] = root.bounds()[2] - 500

        # Create mesh and Actor
        mesh = shapes.Cylinder(pos=[top, pos], c=color, r=radius, alpha=alpha)
        Actor.__init__(self, mesh, name="Cylinder", br_class="Cylinder")
