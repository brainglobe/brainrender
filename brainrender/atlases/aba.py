# import numpy as np
# from tqdm import tqdm

# from vtkplotter import ProgressBar, shapes, merge, load
# from vtkplotter.mesh import Mesh as Actor

# from morphapi.morphology.morphology import Neuron

# import brainrender
# from brainrender.Utils.data_io import load_mesh_from_file, load_json
# from brainrender.Utils.data_manipulation import (
#     get_coords,
#     flatten_list,
#     is_any_item_in_list,
# )

# from brainrender import STREAMLINES_RESOLUTION, INJECTION_VOLUME_SIZE
# from brainrender.Utils.webqueries import request
# from brainrender import *
# from brainrender.Utils import actors_funcs
# from brainrender.colors import (
#     _mapscales_cmaps,
#     makePalette,
#     get_random_colors,
#     getColor,
#     colors,
#     colorMap,
#     check_colors,
# )
# from brainrender.colors import get_n_shades_of

# from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
# from allensdk.api.queries.ontologies_api import OntologiesApi
# from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
# from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
# from allensdk.api.queries.tree_search_api import TreeSearchApi
# from allensdk.core.reference_space_cache import ReferenceSpaceCache

# from brainrender.atlases.base import Atlas


# """
#     THIS CODE IS OUTDATED AND LEFT HERE UNTIL IT'S TRANSFERED TO BRAINGLOBE API ATLAS.
#     The mouse atlases for brainrender are found at brainrender.atlases.mouse

# """

# raise NotImplementedError()


# class ABA(Atlas):
#     """
#     This class handles interaction with the Allen Brain Atlas datasets and APIs to get structure trees,
#     experimental metadata and results, tractography data etc.
#     """

#     ignore_regions = [
#         "retina",
#         "brain",
#         "fiber tracts",
#         "grey",
#     ]  # ignored when rendering

#     # useful vars for analysis

#     atlas_name = "ABA"
#     mesh_format = "obj"

#     def __init__(self, base_dir=None, **kwargs):
#         """
#         Set up file paths and Allen SDKs

#         :param base_dir: path to directory to use for saving data (default value None)
#         :param kwargs: can be used to pass path to individual data folders. See brainrender/Utils/paths_manager.py

#         """

#         Atlas.__init__(self, base_dir=base_dir, **kwargs)
#         self.meshes_folder = (
#             self.mouse_meshes
#         )  # where the .obj mesh for each region is saved

#         # Store all regions metadata [If there's internet connection]
#         if self.other_sets is not None:
#             self.regions = self.other_sets[
#                 "Structures whose surfaces are represented by a precomputed mesh"
#             ].sort_values("acronym")
#             self.region_acronyms = list(
#                 self.other_sets[
#                     "Structures whose surfaces are represented by a precomputed mesh"
#                 ]
#                 .sort_values("acronym")
#                 .acronym.values
#             )

#     # -------------------------- Parents and descendants ------------------------- #

#     # ---------------------------------------------------------------------------- #
#     #                                     UTILS                                    #
#     # ---------------------------------------------------------------------------- #

#     def get_hemispere_from_point(self, p0):
#         if p0[2] > self._root_midpoint[2]:
#             return "right"
#         else:
#             return "left"
