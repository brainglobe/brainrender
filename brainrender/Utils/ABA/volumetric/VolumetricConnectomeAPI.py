import pandas as pd
import numpy as np
import os

from vtkplotter import Volume

try:
    from mcmodels.core import VoxelModelCache
    from mcmodels.core import Mask
except ModuleNotFoundError:
    raise ModuleNotFoundError("To use this functionality you need to install mcmodels "+
                            "with: 'pip install git+https://github.com/AllenInstitute/mouse_connectivity_models.git'")

from brainrender.Utils.paths_manager import Paths
from brainrender.scene import Scene


class VolumetricAPI(Paths):
    projections = {}
    mapped_projections = {}

    hemispheres = dict(left=1, right=2, both=3)


    def __init__(self, base_dir=None, **kwargs):
        Paths.__init__(self, base_dir=base_dir, **kwargs)

        # Load voxel data
        cache_path = os.path.join(self.mouse_connectivity_volumetric, 'voxel_model_manifest.json')

        if not os.path.isfile(cache_path):
            print("Downloading volumetric data. this will take several minutes but it only needs to be done once.")

        self.cache = VoxelModelCache(manifest_file=cache_path)
        self.voxel_array, self.source_mask, self.target_mask = self.cache.get_voxel_connectivity_array()

        # Get structures tree
        self.structure_tree = self.cache.get_structure_tree()

        # Get scene
        self.scene = Scene()

    
    def get_source(self, source, hemisphere='both'):
        if not isinstance(source, list, tuple): 
            source = [source]

        source_ids = [self.structure_tree.get_structures_by_acronym([s])[0]["id"] for s in source]

        self.source = source_mask.get_structure_indices(structure_ids=source_ids, 
                                hemisphere_id=self.hemispheres[hemisphere])
        return self.source

    def get_target(self, target, hemisphere='both'):
        if not isinstance(target, list, tuple): 
            target = [target]

        target_ids = [self.structure_tree.get_structures_by_acronym([s])[0]["id"] for s in target]

        self.target = target_mask.get_structure_indices(structure_ids=target_ids, 
                                hemisphere_id=self.hemispheres[hemisphere])

        self.tgt_mask = Mask.from_cache(self.cache, structure_ids=target_ids, 
                                hemisphere_id=self.hemispheres[hemisphere])
        self.tgt_key = self.tgt_mask.get_key()

        return self.target, self.tgt_mask, self.tgt_key


    def get_projection(self, source, target, name,  **kwargs):
        source = self.get_source(source, **kwargs)
        target, _, _ = self.get_target(target, **kwargs)

        projection = voxel_array[source, target]
        mean_proj = np.mean(projection, axis=0)
        self.projectins[name] = mean_proj
        return mean_proj

    
    def get_mapped_projection(self, source, target, name, **kwargs):
        projection = self.get_projection(source, target, name, **kwargs)
        mapped_projection = self.tgt_mask.map_masked_to_annotation(projection)
        self.mapped_projections[name] = mapped_projection
        return mapped_projection

    def render_mapped_projection(self, source, target, name, 
                        cmap='Greens', alpha=.5,
                        **kwargs):
        mapped_projection = self.get_mapped_projection(source, target, name, **kwargs)

        vol = Volume(mapped_projection)
        lego = vol.legosurface(vmin=np.mean(mapped_projection), vmax=np.max(mapped_projection), 
                    cmap=cmap).alpha(alpha).lw(0)
        return self.scene.add_vtkactor(lego)
    
    def render(self):
        self.scene.render()

