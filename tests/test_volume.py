from brainrender import Scene
import numpy as np
from brainrender.actors import Volume


def test_volume():
    s = Scene(inset=False, root=True)

    data = np.load("examples/data/volume.npy")
    s.add(Volume(data, voxel_size=200, as_surface=False, c="Reds"))
    s.add(Volume(data, voxel_size=200, as_surface=True, c="Reds", mode=2))
    del s

def test_volume_from_file():
    s = Scene(inset=False, root=True)
    s.add(Volume('examples/data/volume.npy', voxel_size=200, as_surface=True, c="Reds", mode=2))
    del s
