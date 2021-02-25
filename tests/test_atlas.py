from brainrender import Scene
from brainrender.actor import Actor
import pytest


@pytest.mark.parametrize(
    "pos, plane, norm",
    [
        (None, "sagittal", None),
        (None, "frontal", [1, 1, 1]),
        ([1000, 1000, 1000], "horizontal", None),
        ([1000, 1000, 1000], None, [0, 1, -1]),
    ],
)
def test_atlas_plane(pos, plane, norm):
    s = Scene()

    p1 = s.atlas.get_plane(plane=plane, pos=pos, norm=norm, sx=1, sy=11)
    p2 = s.atlas.get_plane(plane=plane, pos=pos, norm=norm)
    assert isinstance(p1, Actor)
    assert isinstance(p2, Actor)

    # # s.render(interactive=False)
    del s
