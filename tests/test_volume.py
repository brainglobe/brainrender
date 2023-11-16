import numpy as np

from brainrender import Scene
from brainrender.actors import Volume


def test_volume():
    s = Scene(inset=False, root=True)

    data = np.load("examples/data/volume.npy")
    s.add(Volume(data, voxel_size=200, as_surface=False, c="Reds"))
    s.add(Volume(data, voxel_size=200, as_surface=True, c="Reds"))
    del s
