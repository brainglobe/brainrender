from brainrender import Scene
from brainrender.actors import Point
from morphapi.api.mpin_celldb import MpinMorphologyAPI
from rich.progress import track
from rich import print
from random import choice

from myterial import salmon as c1
from myterial import blue_light as c2

import sys

sys.path.append("./")
from scripts.settings import INSET

N = -1

cam = {
    "pos": (-890, -1818, 979),
    "viewup": (1, -1, -1),
    "clippingRange": (1773, 4018),
    "focalPoint": (478, 210, -296),
    "distance": 2759,
}


print("[bold red]Running: ", __name__)

# -------------------------------- make scene -------------------------------- #

scene = Scene(
    inset=INSET, screenshots_folder="figures", atlas_name="mpin_zfish_1um"
)
scene.root.alpha(0.2)

# -------------------------------- add neurons ------------------------------- #

api = MpinMorphologyAPI()
neurons_ids = api.get_neurons_by_structure(837)
neurons = api.load_neurons(neurons_ids)
neurons = [
    neuron.create_mesh(soma_radius=0.75, neurite_radius=1)
    for neuron in neurons
][:N]

for (neu_dict, neu) in track(neurons, total=N):
    col = choice((c1, c2))
    neuron = scene.add(neu_dict["axon"], alpha=1, color=col)

    soma = scene.add(
        Point(neu_dict["soma"].centerOfMass(), color=col, radius=8, alpha=1)
    )
    scene.add_silhouette(soma)

# ---------------------------------- render ---------------------------------- #

# scene.slice(
#     "sagittal", actors=scene.root,
# )

scene.render(zoom=1.7, camera=cam)
scene.screenshot(name="zfish_neurons")
scene.close()
