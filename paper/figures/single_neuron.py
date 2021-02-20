from brainrender import Scene
import brainrender
from brainrender.actors import Point
from rich import print

brainrender.settings.SHOW_AXES = False

from myterial import blue_grey_light as scmcol
from myterial import blue_grey as pagcol
from myterial import salmon_dark as neuroncol

print("[bold red]Running: ", __name__)

cam = {
    "pos": (-16954, 2456, -3961),
    "viewup": (0, -1, 0),
    "clippingRange": (22401, 34813),
    "focalPoint": (7265, 2199, -5258),
    "distance": 24256,
}

scene = Scene(inset=False, screenshots_folder="figures", root=True)
scene.root._needs_silhouette = False
scene.root.alpha(0.5)
# scene.root.alpha(0)


# neuron.c(black)

pag = scene.add_brain_region("PAG", alpha=0.4, silhouette=False, color=pagcol)
scm = scene.add_brain_region("SCm", alpha=0.3, silhouette=False, color=scmcol)


# -------------------------------- add neurpn -------------------------------- #
neuron = scene.add("data/yulins_neuron.stl")
# neuron.cmap("inferno", 10000 - neuron.points()[:, 1])
neuron.c(neuroncol)


soma_pos = [9350.51912036, 2344.33986638, 5311.18297796]
point = scene.add(Point(soma_pos, color=neuroncol, radius=25))
scene.add_silhouette(point, lw=1, color="k")
scene.add_silhouette(neuron, lw=1, color="k")

# ----------------------------------- slice ---------------------------------- #

p = [9700, 1, 800]
plane = scene.atlas.get_plane(pos=p, plane="frontal")
scene.slice(plane, actors=[scm, pag, scene.root])

p = [11010, 5000, 5705]
plane = scene.atlas.get_plane(pos=p, norm=[0, -1, 0])
scene.slice(plane, actors=[scene.root])

scene.render(zoom=9, camera=cam)
scene.screenshot(name="single_neuron")
scene.close()
