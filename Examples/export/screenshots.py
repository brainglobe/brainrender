""" 
    This tutorial shows how to automatically take screenshots of your rendered region
"""
import time

import brainrender

brainrender.SHADER_STYLE = "cartoon"
from brainrender.scene import Scene

screenshot_params = dict(folder="./screenshots", name="tutorial",)


# Create a scene
scene = Scene(
    screenshot_kwargs=screenshot_params
)  # use screenshot_params to specify where the screenshots will be saved

scene.add_brain_regions(["TH"])

# render
scene.render(
    camera="top", interactive=False
)  # if interactive is false the program won't stop when the scene is rendered
# which means that the next line will be executed
scene.take_screenshot()
time.sleep(1)

# Take another screenshot from a different angle
scene.render(camera="coronal", interactive=False, zoom=0.5)
scene.take_screenshot()  # screenshots are saved with a timestamp in the name so you won't be overwriting the previous one.


# Render interactively. You can then press 's' to take a screenshot
scene.render()
