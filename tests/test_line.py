import numpy as np

from brainrender import Scene
from brainrender.actor import Actor
from brainrender.actors import Line


def test_line():
    s = Scene()

    line = Line(
        np.array(
            [
                [0, 0, 0],
                [1, 1, 1],
                [2, 2, 2],
            ]
        )
    )

    s.add(line)
    assert isinstance(line, Actor)

    del s
