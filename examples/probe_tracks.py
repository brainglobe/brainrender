import os
from pathlib import Path

import numpy as np
from myterial import orange
from rich import print

from brainrender import Scene
from brainrender.actors import Points

data_path = "/home/jingjie/repos/brainrender/brainrender/resources"
# this should be the path of `.npy` files exported from brainglobe-segmentation

scene = Scene(title="Probe Visualization for M-0022")

# Highlight the brain region that we are targetting
cp = scene.add_brain_region("CP", alpha=0.15)
rsp = scene.add_brain_region("RSP", alpha=0.15)

# Add to scene,
# Display the probe track, for each probe that should be a numpy array with coordinations of each sites
scene.add(
    Points(
        np.load(os.path.join(data_path, "probe_1_straitum.npy")),
        name="probe_1",
        colors="darkred",
        radius=50,
    )
)
scene.add(
    Points(
        np.load(os.path.join(data_path, "probe_2_RSC.npy")),
        name="probe_2",
        colors="darkred",
        radius=50,
    )
)
# render
scene.content
scene.render()
