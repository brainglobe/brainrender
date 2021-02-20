from brainrender import Scene
from brainrender.atlas_specific import GeneExpressionAPI
import sys

sys.path.append("./")
from scripts.settings import INSET
from myterial import blue_grey_dark, salmon_dark

from rich import print

print("[bold red]Running: ", __name__)


cam = {
    "pos": (-19159, -6934, -37563),
    "viewup": (0, -1, 0),
    "clippingRange": (24191, 65263),
    "focalPoint": (7871, 2905, -6646),
    "distance": 42229,
}


scene = Scene(inset=INSET, screenshots_folder="figures")
scene.root._needs_silhouette = True
scene.root._silhouette_kwargs["lw"] = 2
scene.root.alpha(0.1)

gene = "Gpr161"
geapi = GeneExpressionAPI()

expids = geapi.get_gene_experiments(gene)
data = geapi.get_gene_data(gene, expids[1])

gene_actor = geapi.griddata_to_volume(data, min_quantile=99, cmap="Reds")
gene_actor.c(salmon_dark)
act = scene.add(gene_actor)

ca1 = scene.add_brain_region(
    "CA1", alpha=0.2, color=blue_grey_dark, silhouette=False
)
ca1.wireframe()

# plane = scene.atlas.get_plane(norm=(0, 0, -1))
# scene.slice(plane, actors=[scene.root])

scene.render(camera=cam, zoom=3.5)
scene.screenshot(name="gene_expression")
