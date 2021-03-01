from brainrender import Scene, Animation
from benchmark.timer import Timer


# Create a brainrender scene
scene = Scene(title="brain regions", inset=False)

with Timer(scene, name="Animation"):
    # Add brain regions

    for br in ("TH", "MOs", "MOp", "CA1", "CB", "MB"):
        scene.add_brain_region(br, silhouette=False)

    anim = Animation(scene, "examples", "vid3")

    # Specify camera position and zoom at some key frames
    # each key frame defines the scene's state after n seconds have passed
    anim.add_keyframe(0, camera="top", zoom=1.3)
    anim.add_keyframe(1, camera="sagittal", zoom=2.1)
    anim.add_keyframe(2, camera="frontal", zoom=3)
    anim.add_keyframe(3, camera="frontal", zoom=2)

    # Make videos
    anim.make_video(duration=3, fps=10)
