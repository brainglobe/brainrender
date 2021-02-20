from PIL import Image, ImageOps
import sys
from myterial import salmon_dark as br1
from myterial import amber as br2
from myterial import orange_dark as br3
from rich import print
from pathlib import Path

from brainrender import Scene

sys.path.append("./")
from paper.figures import INSET

print("[bold red]Running: ", Path(__file__).name)


# camera parameters
cam = {
    "pos": (232278, 99919, -189689),
    "viewup": (0, -1, 0),
    "clippingRange": (615, 1371),
    "focalPoint": (232763, 99854, -188877),
    "distance": 949,
}

# crate a scene with the human atlas
scene = Scene(
    inset=INSET,
    screenshots_folder="paper/screenshots",
    atlas_name="allen_human_500um",
)
scene.root._needs_silhouette = True

# get the subregions of TemL from atlas hierarchy
for main in ("TemL",):
    subs = scene.atlas.get_structure_descendants(main)
    for sub in subs:
        reg = scene.add_brain_region(sub, silhouette=True, color=br1)

# add more brain regions
for reg, col in zip(
    (
        "PrCG",
        "PoCG",
    ),
    (br2, br3),
):
    reg = scene.add_brain_region(reg, silhouette=True, color=col)

# render scene
scene.render(camera=cam, zoom=1.65)
scene.screenshot(name="human_regions")
scene.close()

# Mirror image
im = Image.open("figures/human_regions.png")
im_mirror = ImageOps.mirror(im)
im_mirror.save("figures/human_regions.png")
