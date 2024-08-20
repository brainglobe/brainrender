from brainrender import Animation, Scene, settings
from pathlib import Path

settings.SHOW_AXES = False

scene = Scene(atlas_name="allen_mouse_25um")

regions = (
    "CTX",
    "HPF",
    "STR",
    "CB",
    "MB",
    "TH",
    "HY",
)
scene.add_brain_region(*regions, silhouette=True)


def slc(scene, framen, totframes):
    # Get new slicing plane
    fact = framen / totframes
    shape_um = scene.atlas.shape_um
    # Multiply by fact to move the plane, add buffer to go past the brain
    point = [(shape_um[0] + 500) * fact, shape_um[1] // 2, shape_um[2] // 2]
    plane = scene.atlas.get_plane(pos=point, norm=(1, 0, 0))

    scene.slice(plane)


anim = Animation(
    scene, Path.cwd(), "brainrender_animation_callback", size=None
)

# Specify camera pos and zoom at some key frames`
anim.add_keyframe(0, camera="frontal", zoom=1, callback=slc)

# Make videos
anim.make_video(duration=5, fps=10, fix_camera=True)
