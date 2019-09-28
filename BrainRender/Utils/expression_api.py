import sys
sys.path.append("./")

import pandas as pd

from allensdk.api.queries.mouse_atlas_api import MouseAtlasApi
from allensdk.api.queries.mouse_atlas_api import ReferenceSpaceApi


from BrainRender.settings import *


space = ReferenceSpaceApi()

space.download_mouse_atlas_volume("adult", "atlasvolume", "/Users/federicoclaudi/Dropbox (UCL - SWC)/Rotation_vte/analysis_metadata/anatomy/data.zip")

# matlas = MouseAtlasApi(manifest_file=folders_paths['manifest'])


# genes = matlas.get_genes()
# print(matlas)
# Get mouse genes
# print([x for x in matlas.get_genes()])


# Get experiments ID for a gene
# print(matlas.get_section_data_sets(gene_ids=[114889]))