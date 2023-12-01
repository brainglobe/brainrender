from rich import print as rprint
from vedo import Mesh

from brainrender import Scene
from brainrender.actor import Actor


def test_actor():
    s = Scene()

    s = s.root
    assert isinstance(s, Actor)
    print(s)
    str(s)
    rprint(s)

    assert isinstance(s.mesh, Mesh)
    assert s.alpha() == s.mesh.alpha()
    assert s.name == "root"
    assert s.br_class == "brain region"
