from brainrender import Scene

# import numpy as np

from brainrender.atlas_specific import get_streamlines_for_region
from brainrender.actors.streamlines import Streamlines
import sys
from rich import print

sys.path.append("./")
from scripts.settings import INSET
from myterial import blue_grey
from myterial import salmon_dark as streamlinescol


print("[bold red]Running: ", __name__)

cam = {
    "pos": (9475, -39398, -5604),
    "viewup": (0, 0, -1),
    "clippingRange": (34734, 54273),
    "focalPoint": (7150, 3510, -5283),
    "distance": 42972,
}

scene = Scene(inset=INSET, screenshots_folder="figures")
scene.root._needs_silhouette = True
scene.root._silhouette_kwargs["lw"] = 1
scene.root.alpha(0.5)

streams = get_streamlines_for_region("MOp")
s = scene.add(Streamlines(streams[0], color=streamlinescol, alpha=1))

# pts = s.points()
# mos_com = scene.add_brain_region('MOp', alpha=0).centerOfMass()

# dx = pts[:, 0] - mos_com[0]
# dy = pts[:, 1] - mos_com[1]
# dz = pts[:, 2] - mos_com[2]
# dist = np.sqrt(dx**2 + dy**2 + dz**2)
# s.cmap("viridis", dist)

th = scene.add_brain_region(
    "TH", alpha=0.45, silhouette=False, color=blue_grey
)
# th._silhouette_kwargs["lw"] = 2

scene.slice("horizontal", actors=[scene.root])
# scene.add_silhouette(s, lw=2, color=streamlinescol)

scene.render(camera=cam, zoom=2)
scene.screenshot(name="streamlines")
scene.close()
