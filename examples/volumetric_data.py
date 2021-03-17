"""
    This example shows how to render volumetric (i.e. organized in voxel)
    data in brainrender. The data used are is the localized expression of 
    'Gpr161' from the Allen Atlas database, downloaded with brainrender
    and saved to a numpy file
"""
import numpy as np
from brainrender import Scene
from brainrender import settings

from brainrender.actors import Volume

settings.SHOW_AXES = False


from rich import print
from myterial import orange
from pathlib import Path

print(f"[{orange}]Running example: {Path(__file__).name}")

scene = Scene(inset=False)

data = np.load("examples/data/volume.npy")
print(data.shape)

# make a volume actor and add
actor = Volume(
    "examples/data/volume.npy",
    voxel_size=200,  # size of a voxel's edge in microns
    as_surface=False,  # if true a surface mesh is rendered instead of a volume
    c="Reds",  # use matplotlib colormaps to color the volume
)
scene.add(actor)
scene.render(zoom=1.6)
