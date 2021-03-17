from brainrender import Scene
from brainrender.video import VideoMaker


from rich import print
from myterial import orange
from pathlib import Path

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a scene
scene = Scene("my video")
scene.add_brain_region("TH")

# Create an instance of video maker
vm = VideoMaker(scene, "./examples", "vid1")

# make a video with the custom make frame function
# this just rotates the scene
vm.make_video(elevation=2, duration=2, fps=15)


# Make a custom make frame function
def make_frame(scene, frame_number, *args, **kwargs):
    alpha = scene.root.alpha()
    if alpha < 0.5:
        scene.root.alpha(1)
    else:
        scene.root.alpha(0.2)


# Now make a video with our custom function
scene = Scene("my video2")
scene.add_brain_region("TH")
vm = VideoMaker(scene, "./examples", "vid2", make_frame_func=make_frame)
vm.make_video(duration=1, fps=15)
