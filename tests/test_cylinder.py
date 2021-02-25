from brainrender import Scene
from brainrender.actors import Cylinder


def test_cylinder():
    s = Scene(title="BR")

    th = s.add_brain_region("TH")
    s.add(Cylinder(th, s.root))
    s.add(Cylinder(th.centerOfMass(), s.root))
    del s
