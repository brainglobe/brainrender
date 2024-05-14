"""
    This example shows how to render volumetric (i.e. organized in voxel)
    data in brainrender. The data used are is the localized expression of
    'Gpr161' from the Allen Atlas database, downloaded with brainrender
    and saved to a numpy file
"""

import numpy as np

from brainrender import Scene, settings
from brainrender.actors import Volume

from pathlib import Path

from myterial import orange
from rich import print

settings.SHOW_AXES = False
volume_file = resources_dir = (
    Path(__file__).parent.parent / "resources" / "volume.npy"
)


print(f"[{orange}]Running example: {Path(__file__).name}")

scene = Scene(inset=False)

data = np.load(volume_file)
print(data.shape)

# make a volume actor and add
actor = Volume(
    data,
    voxel_size=200,  # size of a voxel's edge in microns
    as_surface=False,  # if true a surface mesh is rendered instead of a volume
    c="Reds",  # use matplotlib colormaps to color the volume
)
scene.add(actor)
scene.render(zoom=1.6)
