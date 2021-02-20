import brainrender
from brainrender import Scene, Animation
from brainrender.actors import Points
import pandas as pd
import sys

sys.path.append("./")

from scripts.settings import INSET, root_box, SILHOUETTE

brainrender.settings.SHOW_AXES = False


from brainrender.actors.streamlines import make_streamlines
from brainrender.atlas_specific import get_streamlines_for_region
from rich import print

print("[bold red]Running: ", __name__)

cam = {
    "pos": (-2516, 3245, -28274),
    # "focalPoint": (6559, 3823, -5691),
    "viewup": (0, -1, 0),
    # "distance": 24345,
    "clippingRange": (9395, 43223),
    "orientation": (-1, 158, 179),
}
cam2 = {
    "pos": (-9094, -2468, -23245),
    # "focalPoint": (6559, 3823, -5691),
    "viewup": (0, -1, 0),
    # "distance": 24345,
    "clippingRange": (6221, 47218),
    "orientation": (-15, 138, 178),
}
# ---------------------------- keyframes callbacks --------------------------- #


def slce(scene, framen, totframes):
    root, pts, rsp, th, box, roots, rsps, ths = scene.actors

    for act in (roots, rsps, ths):
        scene.actors.pop(scene.actors.index(act))

    # plane = scene.atlas.get_plane(norm=[0, 0, -1])
    scene.slice(
        "sagittal",
        actors=[
            root,
            rsp,
        ],
    )

    root._needs_silhouette = True
    rsp._needs_silhouette = True
    th._needs_silhouette = True


def add_th(scene, framen, totframes):
    scene.add_brain_region(
        "TH", alpha=0.5, silhouette=True, color=[0.6, 0.6, 0.6]
    )


def add_streamlines(scene, framen, totframes):
    scene.add(
        *make_streamlines(
            *streams[1:9], color="steelblue", alpha=0.02, radius=10
        )
    )


def strm_alpha(scene, framen, totframes):
    streams = scene.actors[8:]
    for act in streams:
        alpha = act.alpha()
        act.alpha(alpha + 0.02)


# ------------------------------- create scene ------------------------------- #

scene = Scene(inset=INSET)
scene.root._needs_silhouette = SILHOUETTE
coords = pd.read_hdf("data/cell-detect-paper-cells.h5")
scene.add(Points(coords[["x", "y", "z"]].values, radius=30))
rsp = scene.add_brain_region(
    "RSP",
    alpha=0.5,
    silhouette=SILHOUETTE,
)
scene.add_brain_region(
    "TH",
    alpha=0.15,
    color=[0.6, 0.6, 0.6],
    silhouette=SILHOUETTE,
)
root_box(scene)

# scene.render(interactive=True)

streams = get_streamlines_for_region("RSP")

# ----------------------------- create animation ----------------------------- #

anim = Animation(scene, "videos", "cellfinder", size=None)

# Specify camera pos and zoom at some key frames`
anim.add_keyframe(0, camera="top", zoom=1.3)
anim.add_keyframe(1, camera="top", zoom=1.33, callback=slce, interpol="linear")
anim.add_keyframe(
    2, camera="top", zoom=1.36, callback=add_streamlines, interpol="linear"
)
anim.add_keyframe(
    2.1, camera="top", zoom=1.365, callback=strm_alpha, interpol="linear"
)
anim.add_keyframe(
    2.2, camera="top", zoom=1.37, callback=strm_alpha, interpol="linear"
)
anim.add_keyframe(2.4, camera="top", zoom=1.375, interpol="linear")
anim.add_keyframe(6.8, camera="sagittal2", zoom=1.9)
anim.add_keyframe(7.2, camera="sagittal2", zoom=1.9)
anim.add_keyframe(9.5, camera=cam, zoom=3.5)


# Make videos
anim.make_video(duration=10, fps=30)
