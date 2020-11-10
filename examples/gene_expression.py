from brainrender import Scene
from brainrender.atlas_specific.gene_expression import GeneExpressionAPI

from settings import LW


scene = Scene(inset=False, screenshots_folder="figures")

gene = "Gpr161"
geapi = GeneExpressionAPI()
geneid = geapi.get_gene_id_by_name(gene)
expids = geapi.get_gene_experiments(geneid)
data = geapi.get_gene_data(geneid, expids[1])

gene_actor = geapi.griddata_to_volume(data, min_quantile=99, cmap="inferno")
act = scene.add(gene_actor)

ca1 = scene.add_brain_region("CA1", alpha=0.2, color="skyblue")
ca3 = scene.add_brain_region("CA3", alpha=0.5, color="salmon")


scene.add_silhouette(act, lw=LW)

scene.render(zoom=1.75)
