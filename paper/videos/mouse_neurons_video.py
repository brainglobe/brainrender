from rich import print
import sys
from pathlib import Path

from brainrender import Scene, Animation
from morphapi.api.mouselight import MouseLightAPI
from brainrender.actors import make_neurons

sys.path.append("./")
from paper.figures import INSET, SILHOUETTE

# define three camera positions
cam0 = {
    "pos": (-27734, -17206, 30307),
    "focalPoint": (5703, 3283, -3835),
    "viewup": (0, -1, 0),
    "distance": 51995,
    "clippingRange": (35301, 77678),
}

cam1 = {
    "pos": (6967, -1597, 30135),
    "focalPoint": (4063, 1645, 1110),
    "viewup": (0, -1, 0),
    "distance": 29350,
    "clippingRange": (28096, 49788),
}
cam2 = {
    "pos": (8151, 2782, 30286),
    "focalPoint": (7168, 3838, 971),
    "viewup": (0, -1, 0),
    "distance": 29350,
    "clippingRange": (23584, 51780),
}

print("[bold red]Running: ", Path(__file__).name)


# -------------------------- define frames callback -------------------------- #


def slc(scene, *args):
    """
    Slices some scene actors and makes sure silhouettes are updated
    """
    sils = scene.get_actors(br_class="silhouette")
    scene.remove(*sils)

    mos = scene.get_actors(name="MOs")[0]
    th = scene.get_actors(name="TH")[0]
    sc = scene.get_actors(name="SCm")[0]

    plane = scene.atlas.get_plane(norm=[0, 0, -1])
    scene.slice(plane, actors=[scene.root, th, mos])

    th._needs_silhouette = True
    mos._needs_silhouette = True
    scene.root._needs_silhouette = True
    sc._needs_silhouette = True


# ----------------------------------- Scene ---------------------------------- #

scene = Scene(inset=INSET, screenshots_folder="paper/screenshots")
scene.root._needs_silhouette = SILHOUETTE

# add neruons
mlapi = MouseLightAPI()
neurons_metadata = mlapi.fetch_neurons_metadata(
    filterby="soma", filter_regions=["MOs"]
)

to_add = [neurons_metadata[47], neurons_metadata[51]]
neurons = mlapi.download_neurons(to_add, soma_radius=500)
neurons = scene.add(*make_neurons(*neurons, neurite_radius=12))

# add brain regions
th = scene.add_brain_region("TH", alpha=0.3, silhouette=SILHOUETTE)
mos = scene.add_brain_region("MOs", alpha=0.3, silhouette=SILHOUETTE)
scm = scene.add_brain_region("SCm", alpha=0.3, silhouette=SILHOUETTE)

# ----------------------------- create animation ----------------------------- #

anim = Animation(scene, "videos", "neurons", size=None)

# Specify camera pos and zoom at some key frames`
anim.add_keyframe(0, camera=cam0, zoom=1.8)
anim.add_keyframe(5, camera=cam2, zoom=1.8, callback=slc)
anim.add_keyframe(10, camera=cam1, zoom=3.5)
anim.add_keyframe(15, camera=cam2, zoom=4)

# Make videos
anim.make_video(duration=15, fps=30)
