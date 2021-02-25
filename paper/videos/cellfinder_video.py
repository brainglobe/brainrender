import sys
from rich import print
import numpy as np
from pathlib import Path
from myterial import salmon

import brainrender
from brainrender import Scene, Animation
from brainrender.actors import Points
from brainrender.actors.streamlines import make_streamlines
from brainrender.atlas_specific import get_streamlines_for_region

brainrender.settings.SHOW_AXES = False

sys.path.append("./")
from paper.figures import INSET, root_box, SILHOUETTE


print("[bold red]Running: ", Path(__file__).name)

# define two camera positions
cam = {
    "pos": (-2516, 3245, -28274),
    "viewup": (0, -1, 0),
    "clippingRange": (9395, 43223),
}
cam2 = {
    "pos": (-9094, -2468, -23245),
    "viewup": (0, -1, 0),
    "clippingRange": (6221, 47218),
}


# ---------------------- define frame callback functions --------------------- #


def slce(scene, framen, totframes):
    """
    Slices selected actors and makes sure
    that silhouttes are updated accordingly
    """
    root, pts, rsp, th, box, roots, rsps, ths = scene.actors

    for act in (roots, rsps, ths):
        scene.actors.pop(scene.actors.index(act))

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


def add_streamlines(scene, framen, totframes):
    """
    Adds streamlines to the scene
    """
    scene.add(
        *make_streamlines(
            *streams[1:9], color="steelblue", alpha=0.02, radius=10
        )
    )


def strm_alpha(scene, framen, totframes):
    """
    Incrementally increase streamlines alpaha
    """
    streams = scene.actors[8:]
    for act in streams:
        alpha = act.alpha()
        act.alpha(alpha + 0.02)


# ------------------------------- create scene ------------------------------- #

scene = Scene(inset=INSET)
scene.root._needs_silhouette = SILHOUETTE

coords = np.load("paper/data/cell-detect-paper-cells.npy")
cells = scene.add(Points(coords, radius=30, colors=salmon))

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

# get streamlines data
streams = get_streamlines_for_region("RSP")


# ----------------------------- create animation ----------------------------- #

anim = Animation(scene, "paper/created_videos", "cellfinder", size=None)

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
