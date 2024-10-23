from pathlib import Path

import numpy as np
from myterial import orange
from rich import print

from brainrender import Scene
from brainrender._io import load_mesh_from_file
from brainrender.actor import Actor
from brainrender.actors import Neuron, make_neurons, Points

neuron_file = Path(__file__).parent.parent / "resources" / "neuron1.swc"
obj_file = Path(__file__).parent.parent / "resources" / "CC_134_1_ch1inj.obj"
probe_striatum = (
    Path(__file__).parent.parent / "resources" / "probe_1_striatum.npy"
)

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a brainrender scene
scene = Scene(title="mirrored actors")

# Add the neuron
neuron_original = Neuron(neuron_file)
scene.add(neuron_original)

# Add a mesh from a file
scene.add(obj_file, color="tomato")

# Add a probe from a file
scene.add(
    Points(
        np.load(probe_striatum),
        name="probe_1",
        colors="darkred",
        radius=50,
    ),
    color="darkred",
    radius=50,
)

# Add mirrored objects
axis = "horizontal"
atlas_center = scene.root.center

neuron_mirrored = Neuron(neuron_file)
neuron_mirrored.mirror(axis, origin=atlas_center, atlas=scene.atlas)
scene.add(neuron_mirrored)

mesh_mirrored = Actor(
    load_mesh_from_file(obj_file, color="tomato"),
    name=obj_file.name,
    br_class="from file",
)
mesh_mirrored.mirror(axis, origin=atlas_center, atlas=scene.atlas)
scene.add(mesh_mirrored)

mirrored_probe = Points(
    np.load(probe_striatum),
    name="probe_1",
    colors="darkred",
    radius=50,
)
mirrored_probe.mirror(axis, origin=atlas_center, atlas=scene.atlas)
scene.add(mirrored_probe)

# Render!
scene.render()
