"""
This example shows how to crate an animate scene where
over a number of frames:
    - Different sets of neurons from the mouselight database are shown
    - The camera moves around 

Note that creating videos requires opencv which is not installed
with brainrender by default, please install with "pip install opencv-python"

"""


import brainrender

brainrender.WHOLE_SCREEN = False
brainrender.SHADER_STYLE = "cartoon"
brainrender.ROOT_ALPHA = 0.1


from brainrender.scene import Scene
import numpy as np
from random import choices
from rich.progress import track


from brainrender.Utils.camera import (
    top_camera,
    buildcam,
    sagittal_camera,
)
from brainrender.animation.video import CustomVideoMaker


# --------------------------------- Variables -------------------------------- #
minalpha = 0  # transparency of background neurons
darkcolor = "lightgray"  # background neurons color
lightcolor = "lawngreen"  # highlighted neurons color

N_FRAMES = 250
N_streamlines = (
    -1
)  # number of streamlines to show in total, if -1 all streamlines are shown but it might take a while to render them at first
N_streamlines_in_frame = (
    2  # number of streamlines to be highlighted in a given frame
)
N_frames_for_change = 50  # every N frames which streamlines are shown changes

# Variables to specify camera position at each frame
zoom = np.linspace(1, 1.35, N_FRAMES)
frac = np.zeros_like(
    zoom
)  # for camera transition, interpolation value between cameras
frac[:150] = np.linspace(0, 1, 150)
frac[150:] = np.linspace(1, 0, len(frac[150:]))

# ------------------------------- Create scene ------------------------------- #
scene = Scene(display_inset=True, use_default_key_bindings=True)
root = scene.actors["root"]

filepaths, data = scene.atlas.download_streamlines_for_region("TH")
scene.add_streamlines(data, color="darkseagreen", show_injection_site=False)

scene.add_brain_regions(["TH"], alpha=0.2)

# Make all streamlines background
for mesh in scene.actors["tracts"]:
    mesh.alpha(minalpha)
    mesh.color(darkcolor)


# Create new cameras
cam1 = buildcam(sagittal_camera)
cam2 = buildcam(top_camera)
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
def frame_maker(scene=None, video=None, videomaker=None):
    prev_streamlines = []
    for step in track(
        np.arange(N_FRAMES), total=N_FRAMES, description="Generating frames..."
    ):
        if step % N_frames_for_change == 0:  # change neurons every N framse

            # reset neurons from previous set of neurons
            for mesh in prev_streamlines:
                mesh.alpha(minalpha)
                mesh.color(darkcolor)
            prev_streamlines = []

            # highlight new neurons
            streamlines = choices(
                scene.actors["tracts"], k=N_streamlines_in_frame
            )
            for n, mesh in enumerate(streamlines):
                # color = colorMap(n, 'Reds', vmin=-2, vmax=N_streamlines_in_frame+3)
                mesh.alpha(0.7)
                mesh.color("orangered")
                prev_streamlines.append(mesh)

        # Move scene camera between 3 cameras
        if step < 150:
            scene.plotter.moveCamera(cam1, cam2, frac[step])
        else:
            scene.plotter.moveCamera(cam3, cam2, frac[step])

        # Add frame to video
        scene.render(zoom=zoom[step], interactive=False, video=True)
        video.addFrame()
    return video


# ---------------------------------------------------------------------------- #
#                                  Video maker                                 #
# ---------------------------------------------------------------------------- #
vm = CustomVideoMaker(scene, save_name="streamlines_animation")
vm.make_video(frame_maker)
