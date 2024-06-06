from pathlib import Path

import requests.exceptions
from morphapi.api.mouselight import MouseLightAPI
from myterial import orange
from rich import print

from brainrender import Scene
from brainrender.actors import Neuron, make_neurons

neuron_file = Path(__file__).parent.parent / "resources" / "neuron1.swc"

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a brainrender scene
scene = Scene(title="neurons")

# Add a neuron from file
scene.add(Neuron(neuron_file))

# Download neurons data with morphapi
try:
    mlapi = MouseLightAPI()
    neurons_metadata = mlapi.fetch_neurons_metadata(
        filterby="soma", filter_regions=["MOs"]
    )

    to_add = [neurons_metadata[47], neurons_metadata[51]]
    neurons = mlapi.download_neurons(to_add)
    neurons = scene.add(*make_neurons(*neurons, neurite_radius=12))
except ConnectionError or requests.exceptions.ReadTimeout as e:
    print("Failed to download neurons data from neuromorpho.org.")

# Render!
scene.render()
