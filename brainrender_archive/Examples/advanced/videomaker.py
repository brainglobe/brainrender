from brainrender.animation.video import BasicVideoMaker as VideoMaker
from brainrender.scene import Scene

scene = Scene()

# Create an instance of VideoMaker with our scene
vm = VideoMaker(scene, niters=30)  # niters = number of frames

# Make a video!
vm.make_video(
    elevation=1, roll=5
)  # specify how the scene rotates at each frame
