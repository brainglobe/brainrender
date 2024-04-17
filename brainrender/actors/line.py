from vedo import shapes

from brainrender.actor import Actor


class Line(Actor):
    def __init__(
        self, coordinates, color="black", alpha=1, linewidth=2, name=None
    ):
        """
        Creates an actor representing a single line.

        :param coordinates: list, np.ndarray with shape (N, 3) of ap, dv, ml coordinates.
        :param color: str
        :param alpha: float
        :param linewidth: float
        :param name: str
        """

        # Create mesh and Actor
        mesh = shapes.Line(p0=coordinates, lw=linewidth, c=color, alpha=alpha)
        Actor.__init__(self, mesh, name=name, br_class="Line")
