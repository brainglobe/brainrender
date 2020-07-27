"""
This example shows how to crate an animate scene where
over a number of frames:
    - Different sets of neurons from the mouselight database are shown
    - The camera moves around 
"""


import brainrender

brainrender.WHOLE_SCREEN = False
brainrender.SHADER_STYLE = "cartoon"
brainrender.ROOT_ALPHA = 0.1


from brainrender.scene import Scene
import time
import numpy as np
from random import choices
from rich.progress import track
from morphapi.api.mouselight import MouseLightAPI


from brainrender.Utils.camera import (
    buildcam,
    sagittal_camera,
)
from brainrender.colors import colorMap

# --------------------------------- Variables -------------------------------- #
minalpha = 0.01  # transparency of background neurons
darkcolor = "lightgray"  # background neurons color
lightcolor = "lawngreen"  # highlighted neurons color

N_FRAMES = 250
N_neurons = 50  # number of neurons to show in total, if -1 all neurons are shown but it might take a while to render them at first
N_neurons_in_frame = 8  # number of neurons to be highlighted in a given frame
N_frames_for_change = 15  # every N frames which neurons are shown changes

# Variables to specify camera position at each frame
zoom = np.linspace(1, 1.5, N_FRAMES)
frac = np.zeros_like(
    zoom
)  # for camera transition, interpolation value between cameras
frac[:150] = np.linspace(0, 1, 150)
frac[150:] = np.linspace(1, 0, len(frac[150:]))

# -------------------------------- Fetch data -------------------------------- #

# Then we can download the files and save them as a .json file
ml_api = MouseLightAPI()
# Fetch metadata for neurons with some in the secondary motor cortex
neurons_metadata = ml_api.fetch_neurons_metadata(
    filterby="soma", filter_regions=["MOs"]
)

neurons_files = ml_api.download_neurons(neurons_metadata[:N_neurons])

# ------------------------------- Create scene ------------------------------- #
scene = Scene(display_inset=False, use_default_key_bindings=True)

neurons = scene.add_neurons(neurons_files, neurite_radius=12, alpha=0)

# Make all neurons background
for neuron in neurons:
    for mesh in neuron.values():
        mesh.alpha(minalpha)
        mesh.color(darkcolor)


# Create new cameras
cam1 = buildcam(sagittal_camera)


cam2 = buildcam(
    dict(
        position=[-16624.081, -33431.408, 33527.412],
        focal=[6587.835, 3849.085, 5688.164],
        viewup=[0.634, -0.676, -0.376],
        distance=51996.653,
        clipping=[34765.671, 73812.327],
    )
)

cam3 = buildcam(
    dict(
        position=[1862.135, -4020.792, -36292.348],
        focal=[6587.835, 3849.085, 5688.164],
        viewup=[0.185, -0.97, 0.161],
        distance=42972.44,
        clipping=[29629.503, 59872.10],
    )
)

# Iniziale camera position
startcam = scene.plotter.moveCamera(cam1, cam2, frac[0])


# ------------------------------- Create frames ------------------------------ #
# Create frames
prev_neurons = []
for step in track(
    np.arange(N_FRAMES), total=N_FRAMES, description="Generating frames..."
):
    if step % N_frames_for_change == 0:  # change neurons every N framse

        # reset neurons from previous set of neurons
        for neuron in prev_neurons:
            for component, actor in neuron.items():
                actor.alpha(minalpha)
                actor.color(darkcolor)
        prev_neurons = []

        # highlight new neurons
        neurons = choices(neurons, k=N_neurons_in_frame)
        for n, neuron in enumerate(neurons):
            color = colorMap(
                n, "Greens_r", vmin=-2, vmax=N_neurons_in_frame + 3
            )
            for component, actor in neuron.items():
                actor.alpha(1)
                actor.color(color)
            prev_neurons.append(neuron)

    # Move scene camera between 3 cameras
    scene.plotter.moveCamera(cam1, cam2, frac[step])
    if frac[step] == 1:
        cam1 = cam3

    # Update rendered window
    time.sleep(0.1)
    scene.render(zoom=zoom[step], interactive=False, video=True)
