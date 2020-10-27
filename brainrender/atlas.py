from bg_atlasapi.bg_atlas import BrainGlobeAtlas

from brainrender import settings
from .actor import Actor
from ._io import load_mesh_from_file
from ._utils import return_list_smart


class Atlas(BrainGlobeAtlas):
    def __init__(self, atlas_name=None):
        atlas_name = atlas_name or settings.DEFAULT_ATLAS
        BrainGlobeAtlas.__init__(
            self, atlas_name=atlas_name, print_authors=False
        )

    def get(self, _type, *args, **kwargs):
        # returns Region, Neuron, Streamlines... instances
        if _type == "region":
            return self._get_region(*args, **kwargs)
        else:
            raise ValueError(f"Unrecognized argument {_type}")

    def _get_region(self, *regions, alpha=1, color=None):
        if not regions:
            return None

        actors = []
        for region in regions:
            if region not in self.lookup_df.acronym.values:
                print(
                    f"The region {region} doesn't seem to belong to the atlas being used: {self.atlas_name}. Skipping"
                )
                continue

            # Get mesh
            obj_file = str(self.meshfile_from_structure(region))
            mesh = load_mesh_from_file(obj_file, color=color, alpha=alpha)
            # Todo get for hemisphere only

            # Get color
            if color is None:
                color = [
                    x / 255
                    for x in self._get_from_structure(region, "rgb_triplet")
                ]

            actor = Actor(mesh, name=region, br_class="brain region")
            actor.c(color).alpha(alpha)
            actors.append(actor)

        return return_list_smart(actors)
