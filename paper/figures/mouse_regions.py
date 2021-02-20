from brainrender import Scene
from brainrender.actors import ruler
import sys
import numpy as np

sys.path.append("./")
from scripts.settings import INSET, SILHOUETTE
from myterial import indigo as scmcol
from myterial import indigo_dark as scscol
from myterial import blue_darker as zicol

from rich import print

print("[bold red]Running: ", __name__)

cam = {
    "pos": (-20268, -6818, 14964),
    "viewup": (0, -1, 0),
    "clippingRange": (16954, 58963),
    "focalPoint": (6489, 4329, -5556),
    "distance": 35514,
}

scene = Scene(inset=INSET, screenshots_folder="figures")
scene.root._needs_silhouette = SILHOUETTE

for reg, col in zip(("SCm", "SCs", "ZI"), (scmcol, scscol, zicol)):
    scene.add_brain_region(reg, color=col, silhouette=SILHOUETTE)

bounds = scene.root.bounds()
print(
    f"""
Root dimensions:
    {round((bounds[1]-bounds[0])/1000, 2)} mm
    {round((bounds[3]-bounds[2])/1000, 2)} mm
    {round((bounds[5]-bounds[4])/1000, 2)} mm
"""
)

scene.add(
    ruler(
        np.array([bounds[1], bounds[3], 0]),
        np.array([bounds[2], bounds[3], 0]),
        unit_scale=0.01,
        units="mm",
    )
)


scene.render(zoom=1.75, camera=cam)
# shot(name="mouse_regions", scale=1)
# scene.close()
