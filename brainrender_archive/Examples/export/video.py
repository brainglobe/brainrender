"""
    This tutorial shows how to export a simple video of your scene using the VideoMaker class.
"""

from brainrender.scene import Scene
from brainrender.animation.video import BasicVideoMaker as VideoMaker

scene = Scene()

# Create an instance of VideoMaker with our scene
vm = VideoMaker(scene, niters=30)

# Make a video!
vm.make_video(
    elevation=1, roll=5
)  # specify how the scene rotates at each frame
