import numpy as np
import sys
from rich import print
from pathlib import Path
from myterial import blue_grey as thcol
from myterial import salmon


from brainrender import Scene
from brainrender.actors import Points


sys.path.append("./")
from paper.figures import INSET

print("[bold red]Running: ", Path(__file__).name)

# define camera parmeters
cam = {
    "pos": (5792, 431, 36893),
    "viewup": (0, -1, 0),
    "clippingRange": (39051, 53300),
    "focalPoint": (5865, 4291, -8254),
    "distance": 45311,
}


# make scene
scene = Scene(inset=INSET, screenshots_folder="paper/screenshots")
scene.add_brain_region("TH", alpha=0.2, silhouette=False, color=thcol)

# load cell coordinates and add as a Points actor
coords = np.load("paper/data/cell-detect-paper-cells.npy")
cells = scene.add(Points(coords, radius=30, colors=salmon))

# add a silhouette around the cells
scene.add_silhouette(cells, lw=1)

# slice scene with a sagittal plane
scene.slice("sagittal")

# render and save screenshotq
scene.render(interactive=True, camera="sagittal", zoom=2.6)
scene.screenshot(name="cellfinder_cells")
scene.close()
