from brainrender.scene import Scene
from brainrender.colors import makePalette

from morphapi.api.mpin_celldb import MpinMorphologyAPI


"""
    This examples shows how to download and render neurons
    reconstructions aligned to the zebra fish atlas.
"""

# Use morphapi's API to download the neurons
api = MpinMorphologyAPI()

# the first time you use this dataset you'll have to download the data
# api.download_dataset()

# ----------------------------- Download dataset ----------------------------- #
"""
    If it's the first time using this API, you'll have to download the dataset
    with all of the neurons' data.
"""
# Select a few neurons for a specific brain region
neurons_ids = api.get_neurons_by_structure(837)
neurons = api.load_neurons(neurons_ids)

# Create meshes for each neuron

neurons = [
    neuron.create_mesh(soma_radius=1, neurite_radius=1)[1]
    for neuron in neurons
]
colors = makePalette(len(neurons), "salmon", "powderblue")

# ------------------------------- Visualisation ------------------------------ #
scene = Scene(atlas="mpin_zfish_1um", add_root=True, camera="sagittal2")
scene.add_neurons(neurons, color=colors)
scene.render()
