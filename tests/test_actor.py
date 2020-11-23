from brainrender import Scene
from brainrender.actor import Actor
from vedo import Mesh
from rich import print as rprint


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
