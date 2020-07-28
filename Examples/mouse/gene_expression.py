"""
    This example shows how to download and visualise volumetric
    gene expression data from the Allen Atlas
    dataset: https://mouse.brain-map.org/
"""
from brainrender.scene import Scene
from brainrender.ABA.gene_expression import GeneExpressionAPI


# ---------------------------- Download gene data ---------------------------- #
gene = "Cacna2d1"

geapi = GeneExpressionAPI()  # <- used to download the data from the allen API

"""
    To download a gene's data you need two things:
        - the id of the gene in the allen database
        - the id(s) of the ISH experiments for that gene

    you can get both with GeneExpressionAPI
"""
# Get gene id
geneid = geapi.get_gene_id_by_name(gene)  # 12078

# Get experiment IDs
expids = geapi.get_gene_experiments(
    geneid
)  # [75042246, 72119649, 74000600, 69236915]


"""
    You can then download the data for one of the experiments above
"""
data = geapi.get_gene_data(geneid, expids[0])

"""
    And finally you can take the volumetric data and turn it 
    into an actor that can be added to your brainrender scene.

    When creating the mesh it's useful to set a threshold to eliminate
    voxels with low gene expression energy. This can be done in two ways:
        - [min_value] a user defined threshold value
        - [min_quantile] a percentile (range 0-100): only voxels with value above
                the percentile are rendered.

    You can also pass any matplotlib (or custom) colormap
    to cmap to specify how the voxels will be colored
"""
gene_actor = geapi.griddata_to_volume(data, min_quantile=90, cmap="inferno")


# ---------------------------------- Render ---------------------------------- #

scene = Scene(title=gene)
scene.add_actor(gene_actor)
scene.render()
