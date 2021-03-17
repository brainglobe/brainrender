from brainrender import Scene
from brainrender import settings
from brainrender.atlas_specific import GeneExpressionAPI

from rich import print
from myterial import orange
from pathlib import Path

print(f"[{orange}]Running example: {Path(__file__).name}")

settings.SHOW_AXES = False

scene = Scene(inset=False)

gene = "Gpr161"
geapi = GeneExpressionAPI()
expids = geapi.get_gene_experiments(gene)
data = geapi.get_gene_data(gene, expids[1])

gene_actor = geapi.griddata_to_volume(data, min_quantile=99, cmap="inferno")
act = scene.add(gene_actor)

ca1 = scene.add_brain_region("CA1", alpha=0.2, color="skyblue")
ca3 = scene.add_brain_region("CA3", alpha=0.5, color="salmon")


scene.add_silhouette(act)

scene.render(zoom=1.6)
