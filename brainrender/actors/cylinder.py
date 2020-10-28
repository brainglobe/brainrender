from vedo import shapes

from ..actor import Actor


class Cylinder(Actor):
    def __init__(self, pos, root, color="powderblue", alpha=1, radius=350):
        if isinstance(pos, Actor):
            pos = pos.centerOfMass()

        top = pos.copy()
        top[1] = root.bounds()[2] - 500

        mesh = shapes.Cylinder(pos=[top, pos], c=color, r=radius, alpha=alpha)

        Actor.__init__(self, mesh, name="Cylinder", br_class="Cylinder")
