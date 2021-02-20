from brainrender import Scene
from rich import print

import sys

sys.path.append("./")
from scripts.settings import INSET
from myterial import blue_grey_darker, blue_grey
from myterial import salmon_darker as inj1col
from myterial import salmon_light as inj2col


print("[bold red]Running: ", __name__)


cam = {
    "pos": (-19159, -6934, -37563),
    "viewup": (0, -1, 0),
    "clippingRange": (24191, 65263),
    "focalPoint": (7871, 2905, -6646),
    "distance": 42229,
}


scene = Scene(inset=INSET, screenshots_folder="figures")
scene.root._needs_silhouette = True
scene.root._silhouette_kwargs["lw"] = 1

fs = [
    "data/CC_134_2_ch1inj.obj",
    "data/CC_134_1_ch1inj.obj",
]
cs = [
    inj1col,
    inj2col,
]

scm = scene.add_brain_region(
    "SCm", alpha=0.4, silhouette=False, color=blue_grey_darker
)
scm.wireframe()

pag = scene.add_brain_region(
    "PAG", alpha=0.3, silhouette=False, color=blue_grey
)
pag.wireframe()
# pag._silhouette_kwargs["lw"] = 1

injections = [scene.add(f, color=c) for f, c in zip(fs, cs)]
scene.add(*injections)
scene.add_silhouette(*injections, lw=2)

# inters = injections[0].mesh.intersectWith(injections[1].mesh).lineWidth(LW).c("k")
# scene.add(inters)

scene.render(camera=cam, zoom=3.5)
scene.screenshot(name="injection")
