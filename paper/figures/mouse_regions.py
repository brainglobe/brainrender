import sys
from myterial import indigo as scmcol
from myterial import indigo_dark as scscol
from myterial import blue_darker as zicol
from rich import print
from pathlib import Path

from brainrender import Scene

sys.path.append("./")
from paper.figures import INSET, SILHOUETTE

print("[bold red]Running: ", Path(__file__).name)

# camera settings
cam = {
    "pos": (-20268, -6818, 14964),
    "viewup": (0, -1, 0),
    "clippingRange": (16954, 58963),
    "focalPoint": (6489, 4329, -5556),
    "distance": 35514,
}

# create scene
scene = Scene(inset=INSET, screenshots_folder="paper/screenshots")
scene.root._needs_silhouette = SILHOUETTE

# add brain regions
for reg, col in zip(("SCm", "SCs", "ZI"), (scmcol, scscol, zicol)):
    scene.add_brain_region(reg, color=col, silhouette=SILHOUETTE)

# render
scene.render(zoom=1.75, camera=cam)
scene.screenshot(name="mouse_regions", scale=1)
