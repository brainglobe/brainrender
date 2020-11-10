from brainrender import Scene, Animation

"""
    This example shows how to create an animated video by specifying
    the camera parameters at a number of key frames
"""

# Create a brainrender scene
scene = Scene(title="brain regions", inset=False)

# Add brain regions
scene.add_brain_region("TH")

anim = Animation(scene, "examples", "vid3")

# Specify camera position and zoom at some key frames
anim.add_keyframe(0, camera="top", zoom=1.3)
anim.add_keyframe(10, camera="sagittal", zoom=2.1)
anim.add_keyframe(20, camera="frontal", zoom=3)
anim.add_keyframe(30, camera="frontal", zoom=2)

# Make videos
anim.make_video(duration=3, fps=10)
