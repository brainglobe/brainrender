from pathlib import Path
from rich import print
import sys

from brainrender import Scene, Animation

sys.path.append("./")
from paper.figures import INSET, root_box, SILHOUETTE

print("[bold red]Running: ", Path(__file__).name)


# -------------------------- define frames callback -------------------------- #
def slc(scene, framen, totframes):
    """
    Slices all actors at increasingly more caudal locatons
    Ensures silhouttes are updated
    """
    # remove silhouettes
    scene.remove(*scene.get_actors(br_class="silhouette"))

    # Get new slicing plane
    fact = framen / totframes
    point = [14000 * fact, 4000, 6000]
    plane = scene.atlas.get_plane(pos=point, norm=(1, 0, 0))

    # slice
    box = scene.get_actors(name="box")[0]
    acts = [a for a in scene.actors if a != box]
    scene.slice(plane, actors=acts)

    # make new silhouettes
    for act in scene.get_actors(br_class="brain region"):
        act._needs_silhouette = True


# ------------------------------- Create scene ------------------------------- #

scene = Scene(inset=INSET)
scene.root._needs_silhouette = SILHOUETTE

# add transparent box around root to preserve camera position
root_box(scene)

# add all brain regions
mains = (
    "Isocortex",
    "HPF",
    "STR",
    "PAL",
    "CB",
    "MB",
    "TH",
    "HY",
    "P",
    "MY",
    "CTXsp",
    "OLF",
    "VISC",
)

for main in mains:
    subs = scene.atlas.get_structure_descendants(main)

    for sub in subs:
        try:
            reg = scene.add_brain_region(sub, silhouette=SILHOUETTE)
        except FileNotFoundError:
            pass


# ----------------------------- create animation ----------------------------- #
anim = Animation(scene, "videos", "regions", size=None)

anim.add_keyframe(0, camera="frontal", zoom=1.5, callback=slc, duration=10)

anim.make_video(duration=10, fps=30)
