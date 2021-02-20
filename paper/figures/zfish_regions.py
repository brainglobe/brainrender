from rich import print
from myterial import cyan as cbcol
from myterial import teal as tcol
import sys
from pathlib import Path

from brainrender import Scene

sys.path.append("./")
from paper.figures import INSET, SILHOUETTE

print("[bold red]Running: ", Path(__file__).name)

# camera settings
cam = {
    "pos": (-1122, -389, 1169),
    "viewup": (0, -1, 0),
    "clippingRange": (1168, 3686),
    "focalPoint": (469, 221, -346),
    "distance": 2280,
}

# create scene
scene = Scene(
    inset=INSET,
    screenshots_folder="paper/screenshots",
    atlas_name="mpin_zfish_1um",
)
scene.root._needs_silhouette = SILHOUETTE
scene.root._silhouette_kwargs["lw"] = 3
scene.root.alpha(0.2)

# add brain regions
cb, t = scene.add_brain_region("cerebellum", "tectum", silhouette=SILHOUETTE)
cb.c(cbcol)
t.c(tcol)

# render
scene.render(zoom=1.9, camera=cam)
scene.screenshot(name="zfish_regions")
scene.close()
