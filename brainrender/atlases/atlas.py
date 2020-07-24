from bg_atlasapi.bg_atlas import BrainGlobeAtlas

import brainrender
from brainrender.Utils.paths_manager import Paths
from brainrender.atlases.aba import ABA
from brainrender.atlases.base import Base


class Atlas(BrainGlobeAtlas, Paths, Base, ABA):
    _planes_norms = dict(  # normals of planes cutting through the scene along
        # orthogonal axes. These values must be replaced if atlases
        # are oriented differently.
        sagittal=[0, 0, 1],
        coronal=[1, 0, 0],
        horizontal=[0, 1, 0],
    )

    def __init__(self, *args, base_dir=None, **kwargs):
        # Create brainglobe atlas
        name = kwargs.pop("atlas_name", None)
        if name is None:
            name = brainrender.DEFAULT_ATLAS

        BrainGlobeAtlas.__init__(self, *args, atlas_name=name, **kwargs)

        # Add brainrender paths
        Paths.__init__(self, base_dir=base_dir, **kwargs)
        self.meshes_folder = (
            None  # where the .obj mesh for each region is saved
        )

        # Add base atlas functionality
        Base.__init__(self)

        # If it's a mouse atlas, add extra functionality
        if "Mus musculus" == self.metadata["species"]:
            ABA.__init__(self)
