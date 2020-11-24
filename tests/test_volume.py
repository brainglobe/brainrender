from brainrender import Scene
import numpy as np
from brainrender.actors import Volume


def test_volume():
    scene = Scene(inset=False, root=True)

    data = np.load("examples/data/volume.npy")
    scene.add(Volume(data, voxel_size=200, as_surface=False, c="Reds"))
    scene.add(Volume(data, voxel_size=200, as_surface=True, c="Reds", mode=2))

    scene.render(interactive=False)
