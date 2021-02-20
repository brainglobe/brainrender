from brainrender import Scene
from brainrender.actors import Points
from oneibl.onelight import ONE
from PIL import Image, ImageOps

import sys

sys.path.append("./")
from scripts.settings import (
    INSET,
    SILHOUETTE,
)
from myterial import blue_grey, blue_grey_dark, salmon_light, salmon_darker

from rich import print

print("[bold red]Running: ", __name__)

cam = {
    "pos": (-16170, -7127, 31776),
    "viewup": (0, -1, 0),
    "clippingRange": (27548, 67414),
    "focalPoint": (7319, 2861, -3942),
    "distance": 43901,
}


scene = Scene(inset=INSET, screenshots_folder="figures")
scene.root._needs_silhouette = True
scene.root._silhouette_kwargs["lw"] = 1
scene.root.alpha(0.2)

one = ONE()
one.set_figshare_url("https://figshare.com/articles/steinmetz/9974357")

# select sessions with trials
sessions = one.search(["trials"])

probes_locs = []
for sess in sessions:
    probes_locs.append(one.load_dataset(sess, "channels.brainLocation"))

for locs in probes_locs:
    k = int(len(locs) / 374.0)

    for i in range(k):
        points = locs[i * 374 : (i + 1) * 374]
        regs = points.allen_ontology.values

        if "LGd" in regs and ("VISa" in regs or "VISp" in regs):
            color = salmon_darker
            alpha = 1
            sil = 1
        elif "VISa" in regs:
            color = salmon_light
            alpha = 1
            sil = 0.5
        else:
            continue

        spheres = Points(
            points[["ccf_ap", "ccf_dv", "ccf_lr"]].values,
            colors=color,
            alpha=alpha,
            radius=30,
        )
        spheres = scene.add(spheres)

        if SILHOUETTE and sil:
            scene.add_silhouette(spheres, lw=sil)


# Add brain regions
visp, lgd = scene.add_brain_region(
    "VISp",
    "LGd",
    hemisphere="right",
    alpha=0.3,
    silhouette=False,
    color=blue_grey_dark,
)
visa = scene.add_brain_region(
    "VISa",
    hemisphere="right",
    alpha=0.2,
    silhouette=False,
    color=blue_grey,
)
th = scene.add_brain_region(
    "TH", alpha=0.3, silhouette=False, color=blue_grey_dark
)
th.wireframe()
scene.add_silhouette(lgd, visp, lw=2)


scene.render(zoom=3.5, camera=cam)
scene.screenshot(name="probes")
scene.close()

# Mirror image
im = Image.open("figures/probes.png")
im_mirror = ImageOps.mirror(im)
im_mirror.save("figures/probes.png")
