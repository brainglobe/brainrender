from brainrender import Scene
from brainrender.actors import Points  # , PointsDensity
import pandas as pd
import sys

sys.path.append("./")

from scripts.settings import INSET
from rich import print

from myterial import blue_grey as thcol
from myterial import salmon


print("[bold red]Running: ", __name__)

cam = {
    "pos": (5792, 431, 36893),
    "viewup": (0, -1, 0),
    "clippingRange": (39051, 53300),
    "focalPoint": (5865, 4291, -8254),
    "distance": 45311,
}


# -------------------------------- make scene -------------------------------- #

scene = Scene(inset=INSET, screenshots_folder="figures")


coords = pd.read_hdf("data/cell-detect-paper-cells.h5")
cells = scene.add(
    Points(coords[["x", "y", "z"]].values, radius=30, colors=salmon)
)
scene.add_silhouette(cells, lw=1)


scene.add_brain_region("TH", alpha=0.2, silhouette=False, color=thcol)


# ------------------------------ cut and render ------------------------------ #
scene.slice("sagittal")


scene.render(camera="sagittal", zoom=2.6)
scene.screenshot(name="cellfinder_cells")
scene.close()
