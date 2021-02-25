import sys
from myterial import blue_grey_dark, salmon_dark
from rich import print
from pathlib import Path

from brainrender import Scene
from brainrender.atlas_specific import GeneExpressionAPI

sys.path.append("./")
from paper.figures import INSET

print("[bold red]Running: ", Path(__file__).name)


# camera parameters
cam = {
    "pos": (-19159, -6934, -37563),
    "viewup": (0, -1, 0),
    "clippingRange": (24191, 65263),
    "focalPoint": (7871, 2905, -6646),
    "distance": 42229,
}

# create scene
scene = Scene(inset=INSET, screenshots_folder="paper/screenshots")

# add silhouette to root and change alpha
scene.root._needs_silhouette = True
scene.root._silhouette_kwargs["lw"] = 2
scene.root.alpha(0.1)

# download gene expression data
gene = "Gpr161"
geapi = GeneExpressionAPI()
expids = geapi.get_gene_experiments(gene)
data = geapi.get_gene_data(gene, expids[1])

# createa a Volume actor and add to scene
gene_actor = geapi.griddata_to_volume(data, min_quantile=99, cmap="Reds")
gene_actor.c(salmon_dark)
act = scene.add(gene_actor)

# add CA1 as wireframe
ca1 = scene.add_brain_region(
    "CA1", alpha=0.2, color=blue_grey_dark, silhouette=False
)
ca1.wireframe()

# render
scene.render(camera=cam, zoom=3.5)
scene.screenshot(name="gene_expression")
