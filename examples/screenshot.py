from pathlib import Path

from myterial import orange, salmon
from rich import print

from brainrender import Scene

print(f"[{orange}]Running example: {Path(__file__).name}")

# Explicitly initiliase a scene with the screenshot folder set
# If the screenshot folder is not set, by default screenshots
# Will save to the current working directory
screenshot_folder = "./examples/screenshots"
scene = Scene(
    title=f"Screenshots will be saved to {screenshot_folder}",
    inset=True,
    screenshots_folder=screenshot_folder,
)

# Add some actors to the scene
scene.add_brain_region("TH", alpha=0.2, silhouette=True, color=salmon)
scene.add_brain_region("VISp", alpha=0.4, silhouette=False, color=[50, 2, 155])

scene.slice("sagittal")

# Set up a camera. Can use string, such as "sagittal".
# During render runtime, press "c" to print the current camera parameters.
camera = {
    "pos": (8777, 1878, -44032),
    "viewup": (0, -1, 0),
    "clippingRange": (24852, 54844),
    "focalPoint": (7718, 4290, -3507),
    "distance": 40610,
}
zoom = 1.5

# If you only want a screenshot and don't want to move the camera
# around the scene, set interactive to False.
scene.render(interactive=False, camera=camera, zoom=zoom)

# Set the scale, which will be used for screenshot resolution.
# Any value > 1 increases resolution, the default is in brainrender.settings.
# It is easiest integer scales (non-integer can cause crashes).
scale = 2

# Take a screenshot - passing no name uses current time
# Screenshots can be also created during runtime by pressing "s"
scene.screenshot(name="example_brainrender_shot", scale=scale)

scene.close()
