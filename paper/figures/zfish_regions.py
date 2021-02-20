from brainrender import Scene
from rich import print

import sys

sys.path.append("./")
from scripts.settings import INSET, SILHOUETTE
from myterial import cyan as cbcol
from myterial import teal as tcol


print("[bold red]Running: ", __name__)

cam = {
    "pos": (-1122, -389, 1169),
    "viewup": (0, -1, 0),
    "clippingRange": (1168, 3686),
    "focalPoint": (469, 221, -346),
    "distance": 2280,
}

scene = Scene(
    inset=INSET, screenshots_folder="figures", atlas_name="mpin_zfish_1um"
)
scene.root._needs_silhouette = SILHOUETTE
scene.root._silhouette_kwargs["lw"] = 3
scene.root.alpha(0.2)

cb, t = scene.add_brain_region("cerebellum", "tectum", silhouette=SILHOUETTE)
cb.c(cbcol)
t.c(tcol)

bounds = scene.root.bounds()
print(
    f"""
Root dimensions:
    {round((bounds[1]-bounds[0])/1000, 2)} mm
    {round((bounds[3]-bounds[2])/1000, 2)} mm
    {round((bounds[5]-bounds[4])/1000, 2)} mm
"""
)


scene.render(zoom=1.9, camera=cam)
scene.screenshot(name="zfish_regions")
scene.close()
