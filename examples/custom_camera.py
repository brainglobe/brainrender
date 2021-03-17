"""
    This example shows how to create a scene and render it with a custom camera.
    This is done by specifying a dictionary of camera parameters, to get the 
    parameters you need for your camera:
    - render an interactive scene with any camera
    - move the camera to where you need it to be
    - press 'c'
    - this will print the current camera parameters to your console. Copy paste the
        parameters in your script
"""

from brainrender import Scene

from rich import print
from myterial import orange
from pathlib import Path

print(f"[{orange}]Running example: {Path(__file__).name}")

custom_camera = {
    "pos": (41381, -16104, 27222),
    "viewup": (0, -1, 0),
    "clippingRange": (31983, 76783),
}


# Create a brainrender scene
scene = Scene(title="Custom camera")

# Add brain regions
scene.add_brain_region("CB", alpha=0.8)

# Render!
scene.render(camera=custom_camera, zoom=1.5)
