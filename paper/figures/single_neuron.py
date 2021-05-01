from rich import print
from pathlib import Path
from brainrender import Scene
from myterial import blue_grey_light as scmcol
from myterial import blue_grey as pagcol
from myterial import salmon_dark as neuroncol

import brainrender
from brainrender.actors import Point

brainrender.settings.SHOW_AXES = False

print("[bold red]Running: ", Path(__file__).name)

# camera settings
cam = {
    "pos": (-16954, 2456, -3961),
    "viewup": (0, -1, 0),
    "clippingRange": (22401, 34813),
    "focalPoint": (7265, 2199, -5258),
    "distance": 24256,
}

# create scene
scene = Scene(inset=False, screenshots_folder="paper/screenshots", root=True)
scene.root._needs_silhouette = False
scene.root.alpha(0.5)

# add brain regions
pag = scene.add_brain_region("PAG", alpha=0.4, silhouette=False, color=pagcol)
scm = scene.add_brain_region("SCm", alpha=0.3, silhouette=False, color=scmcol)

# add neuron mesh
neuron = scene.add("paper/data/yulins_neuron.stl")
neuron.c(neuroncol)

# add sphere at soma location
soma_pos = [9350.51912036, 2344.33986638, 5311.18297796]
point = scene.add(Point(soma_pos, color=neuroncol, radius=25))
scene.add_silhouette(point, lw=1, color="k")
scene.add_silhouette(neuron, lw=1, color="k")

# slice scene repeatedly to cut out region of interest
p = [9700, 1, 800]
plane = scene.atlas.get_plane(pos=p, plane="frontal")
scene.slice(plane, actors=[scm, pag, scene.root])

p = [11010, 5000, 5705]
plane = scene.atlas.get_plane(pos=p, norm=[0, -1, 0])
scene.slice(plane, actors=[scene.root])

# render
scene.render(zoom=9, camera=cam)
scene.screenshot(name="single_neuron")
scene.close()
