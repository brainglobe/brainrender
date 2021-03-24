from brainrender import Scene, Animation


from rich import print
from myterial import orange
from pathlib import Path

import brainrender

brainrender.set_logging("DEBUG")

print(f"[{orange}]Running example: {Path(__file__).name}")

"""
    This example shows how to create an animated video by specifying
    the camera parameters at a number of key frames
"""

# Create a brainrender scene
scene = Scene(title="brain regions", inset=False)

# Add brain regions
scene.add_brain_region("TH")

anim = Animation(scene, "./examples", "vid3")

# Specify camera position and zoom at some key frames
# each key frame defines the scene's state after n seconds have passed
anim.add_keyframe(0, camera="top", zoom=1.3)
anim.add_keyframe(1, camera="sagittal", zoom=3)
anim.add_keyframe(2, camera="frontal", zoom=0.8)
anim.add_keyframe(
    3,
    camera="frontal",
)

# Make videos
anim.make_video(duration=3, fps=10)
