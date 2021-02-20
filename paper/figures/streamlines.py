import sys
from rich import print
from pathlib import Path
from myterial import blue_grey
from myterial import salmon_dark as streamlinescol

from brainrender import Scene
from brainrender.atlas_specific import get_streamlines_for_region
from brainrender.actors.streamlines import Streamlines

sys.path.append("./")
from paper.figures import INSET

print("[bold red]Running: ", Path(__file__).name)

# camera parameters
cam = {
    "pos": (9475, -39398, -5604),
    "viewup": (0, 0, -1),
    "clippingRange": (34734, 54273),
    "focalPoint": (7150, 3510, -5283),
    "distance": 42972,
}

# create scene
scene = Scene(inset=INSET, screenshots_folder="paper/screenshots")
scene.root._needs_silhouette = True
scene.root._silhouette_kwargs["lw"] = 1
scene.root.alpha(0.5)

# get streamlines data
streams = get_streamlines_for_region("MOp")

# add Streamlines actors
s = scene.add(Streamlines(streams[0], color=streamlinescol, alpha=1))

# add brain regions
th = scene.add_brain_region(
    "TH", alpha=0.45, silhouette=False, color=blue_grey
)

# slice scene
scene.slice("horizontal", actors=[scene.root])

# render
scene.render(camera=cam, zoom=2)
scene.screenshot(name="streamlines")
scene.close()
