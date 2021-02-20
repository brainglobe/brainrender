from brainrender import Scene
from morphapi.api.mouselight import MouseLightAPI
from scripts.settings import INSET, SILHOUETTE

from myterial import blue_grey_dark as thcol
from myterial import salmon_dark, salmon_darker, orange_darker, grey_darker

from rich import print

print("[bold red]Running: ", __name__)

cam = {
    "pos": (5892, 1302, 23377),
    "viewup": (0, -1, 0),
    "clippingRange": (22662, 41078),
    "focalPoint": (5943, 3955, -5680),
    "distance": 29178,
}

scene = Scene(inset=INSET, screenshots_folder="figures")
scene.root._needs_silhouette = SILHOUETTE
mlapi = MouseLightAPI()
neurons_metadata = mlapi.fetch_neurons_metadata(
    filterby="soma", filter_regions=["MOs"]
)

to_add = [neurons_metadata[47], neurons_metadata[51], neurons_metadata[60]]
neurons = mlapi.download_neurons(to_add, soma_radius=500)

colors = (salmon_dark, salmon_darker, orange_darker)
for neuron, color in zip(neurons, colors):
    meshes = neuron.create_mesh(soma_radius=35, neurite_radius=10)[0]
    dendrites = scene.add(meshes["basal_dendrites"], color=grey_darker)
    soma = scene.add(meshes["soma"], color=grey_darker)
    axon = scene.add(meshes["axon"], color=color)


th = scene.add_brain_region("TH", alpha=0.1, color=thcol)


scene.slice("sagittal", actors=[scene.root, th])


scene.render(zoom=2.6, camera=cam)
scene.screenshot(name="mouse_neurons")

scene.close()
