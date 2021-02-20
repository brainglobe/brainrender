from rich import print
from myterial import blue_grey_darker, blue_grey
from myterial import salmon_darker as inj1col
from myterial import salmon_light as inj2col
from pathlib import Path
import sys

from brainrender import Scene

sys.path.append("./")
from paper.figures import INSET

print("[bold red]Running: ", Path(__file__).name)


# camera parameters
cam = {
    "pos": (-19159, -6934, -37563),
    "viewup": (0, -1, 0),
    "clippingRange": (24191, 65263),
    "focalPoint": (7871, 2905, -6646),
    "distance": 42229,
}

# create scene and makes sure root has silhouette
scene = Scene(inset=INSET, screenshots_folder="paper/screenshots")
scene.root._needs_silhouette = True
scene.root._silhouette_kwargs["lw"] = 1

# add meshes from file
files = [
    "paper/data/CC_134_2_ch1inj.obj",
    "paper/data/CC_134_1_ch1inj.obj",
]
colors = [
    inj1col,
    inj2col,
]
injections = [scene.add(f, color=c) for f, c in zip(files, colors)]
scene.add_silhouette(*injections, lw=2)

# add brain regions
scm = scene.add_brain_region(
    "SCm", alpha=0.4, silhouette=False, color=blue_grey_darker
)
pag = scene.add_brain_region(
    "PAG", alpha=0.3, silhouette=False, color=blue_grey
)

# make brain region as wireframe
scm.wireframe()
pag.wireframe()

# render
scene.render(camera=cam, zoom=3.5)
scene.screenshot(name="injection")
