import numpy as np

from benchmark.timer import Timer
from brainrender import Scene
from brainrender.actors import Volume

scene = Scene(inset=False)
data = np.load("benchmark/volume.npy")

with Timer(scene, name="Render volume"):
    for i in range(10):
        actor = Volume(
            data,
            voxel_size=200,  # size of a voxel's edge in microns
            as_surface=False,  # if true a surface mesh is rendered instead of a volume
            c="Reds",  # use matplotlib colormaps to color the volume
        )
        scene.add(actor)
