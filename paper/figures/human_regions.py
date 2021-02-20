from brainrender import Scene
from PIL import Image, ImageOps
import sys

sys.path.append("./")
from scripts.settings import INSET, SILHOUETTE
from myterial import salmon_dark as br1
from myterial import amber as br2
from myterial import orange_dark as br3

from rich import print

print("[bold red]Running: ", __name__)


cam = {
    "pos": (232278, 99919, -189689),
    "viewup": (0, -1, 0),
    "clippingRange": (615, 1371),
    "focalPoint": (232763, 99854, -188877),
    "distance": 949,
}


scene = Scene(
    inset=INSET,
    screenshots_folder="figures",
    atlas_name="allen_human_500um",
)
scene.root._needs_silhouette = SILHOUETTE

for main in ("TemL",):  # "ParL", "OccL",
    subs = scene.atlas.get_structure_descendants(main)
    for sub in subs:
        reg = scene.add_brain_region(sub, silhouette=SILHOUETTE, color=br1)

for reg, col in zip(
    (
        "PrCG",
        "PoCG",
    ),
    (br2, br3),
):
    reg = scene.add_brain_region(reg, silhouette=SILHOUETTE, color=col)

print(reg.bounds())
bounds = scene.root.bounds()
print(bounds)
print(
    f"""
Root dimensions:
    {round((bounds[1]-bounds[0])/1000, 2)} mm
    {round((bounds[3]-bounds[2])/1000, 2)} mm
    {round((bounds[5]-bounds[4])/1000, 2)} mm
"""
)

scene.render(camera=cam, zoom=1.65)
scene.screenshot(name="human_regions")
scene.close()


# Mirror image
im = Image.open("figures/human_regions.png")
im_mirror = ImageOps.mirror(im)
im_mirror.save("figures/human_regions.png")
