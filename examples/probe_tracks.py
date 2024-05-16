"""
This example visualizes `.npy` files exported from brainglobe-segmentation
"""

from pathlib import Path
import numpy as np

from brainrender import Scene
from brainrender.actors import Points

resource_path = Path(__file__).parent.parent / "resources"

scene = Scene(title="Silicon Probe Visualization")

# Visualise the probe target regions
cp = scene.add_brain_region("CP", alpha=0.15)
rsp = scene.add_brain_region("RSP", alpha=0.15)

# Add probes to the scene.
# Each .npy file should contain a numpy array with the coordinates of each
# part of the probe.
scene.add(
    Points(
        np.load(resource_path / "probe_1_striatum.npy"),
        name="probe_1",
        colors="darkred",
        radius=50,
    )
)
scene.add(
    Points(
        np.load(resource_path / "probe_2_RSP.npy"),
        name="probe_2",
        colors="darkred",
        radius=50,
    )
)

# render
scene.render()
