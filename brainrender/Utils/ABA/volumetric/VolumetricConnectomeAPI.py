import numpy as np
import os

from vtkplotter import Volume

# TODO see if this can be added to setup.py
try:
    from mcmodels.core import VoxelModelCache
    from mcmodels.core import Mask
except ModuleNotFoundError:
    raise ModuleNotFoundError("To use this functionality you need to install mcmodels "+
                            "with: 'pip install git+https://github.com/AllenInstitute/mouse_connectivity_models.git'")

from brainrender.Utils.paths_manager import Paths
from brainrender.scene import Scene

# TODO document mcmodels source + reference

class VolumetricAPI(Paths):
    projections = {}
    mapped_projections = {}

    hemispheres = dict(left=1, right=2, both=3)

    def __init__(self, base_dir=None, add_root=True, scene_kwargs={}, **kwargs):
        Paths.__init__(self, base_dir=base_dir, **kwargs)

        # Get MCM cache
        cache_path = os.path.join(self.mouse_connectivity_volumetric, 'voxel_model_manifest.json')

        if not os.path.isfile(cache_path):
            print("Downloading volumetric data. This will take several minutes but it only needs to be done once.")

        self.cache = VoxelModelCache(manifest_file=cache_path)
        self.voxel_array = None

        # Get projection cache paths
        self.data_cache = self.mouse_connectivity_volumetric_cache
        self.data_cache_projections = os.path.join(self.data_cache, "projections")
        self.data_cache_targets = os.path.join(self.data_cache, "targets")
        self.data_cache_sources = os.path.join(self.data_cache, "sources")

        for fold in [self.data_cache_projections, self.data_cache_targets, self.data_cache_sources]:
            if not os.path.isdir(fold):
                os.mkdir(fold)

        # Get structures tree
        self.structure_tree = self.cache.get_structure_tree()

        # Get scene
        self.scene = Scene(add_root=add_root, **scene_kwargs)

    def _get_structure_id(self, struct):
        if not isinstance(struct, (list, tuple)): 
            struct = [struct]
        return [self.structure_tree.get_structures_by_acronym([s])[0]["id"] for s in struct]

    def _load_voxel_data(self):
        if self.voxel_array is None:
            print("Loading voxel data, might take a few minutes.")
            self.voxel_array, self.source_mask, self.target_mask = self.cache.get_voxel_connectivity_array()

    def _get_cache_filename(self, tgt, what):
        if what == 'projection':
            fld = self.data_cache_projections
        elif what == 'source':
            fld = self.data_cache_sources
        elif what == 'target':
            fld = self.data_cache_targets
        else:
            raise ValueError(f'Error while getting cached data file name.\n'+
                            f'What was {what} but should be projection/source/target.')

        name = ''.join([str(i) for i in tgt])
        path = os.path.join(fld, name+'.npy')
        return name, path, os.path.isfile(path)

    def _get_from_cache(self, tgt, what):
        name, cache_path, cache_exists = self._get_cache_filename(tgt, what)
        if not cache_exists:
            return None
        else:
            return np.load(cache_path)

    def save_to_cache(self, tgt, what, obj):
        name, cache_path, cache_exists = self._get_cache_filename(tgt, what)
        np.save(cache_path, obj)

    def get_source(self, source, hemisphere='both'):
        """
            Loads the mask for a source structure

            :param source: str or list of str with acronym of source regions
            :param hemisphere: str, ['both', 'left', 'right']. Which hemisphere to consider.
        """
        if not isinstance(source, (list, tuple)): 
            source = [source]

        self.source = self._get_from_cache(source, 'source')
        if self.source is None:
            self._load_voxel_data()
            source_ids = self._get_structure_id(source)

            self.source = self.source_mask.get_structure_indices(structure_ids=source_ids, 
                                    hemisphere_id=self.hemispheres[hemisphere])
            self.save_to_cache(source, 'source', self.source)
        return self.source

    def get_target_mask(self, target, hemisphere):
        target_ids = self._get_structure_id(target)
        self.tgt_mask = Mask.from_cache(self.cache, structure_ids=target_ids, 
                        hemisphere_id=self.hemispheres[hemisphere])
        self.tgt_key = self.tgt_mask.get_key()

    def get_target(self, target, hemisphere='both'):
        """
            Loads the mask for a target structure. Also returs a 'key' array and a mask object
            used to transform projection data from linear arrays to 3D volumes.

            :param target: str or list of str with acronym of target regions
            :param hemisphere: str, ['both', 'left', 'right']. Which hemisphere to consider.
        """
        if not isinstance(target, (list, tuple)): 
            target = [target]

        self.target = self._get_from_cache(target, 'target')
        if self.target is None:
            self._load_voxel_data()
            target_ids = self._get_structure_id(target)

            self.target = self.target_mask.get_structure_indices(structure_ids=target_ids, 
                                    hemisphere_id=self.hemispheres[hemisphere])
            self.save_to_cache(target, 'target', self.target)

        self.get_target_mask(target, hemisphere)
        return self.target

    def get_projection(self, source, target, name,  hemisphere='both', projection_mode='mean', ):
        """
                Gets the spatialised projection intensity from a source to a target. 

                :param source: str or list of str with acronym of source regions
                :param target: str or list of str with acronym of target regions
                :param name: str, name of the projection

                :return: 1D numpy array with mean projection from source to target voxels
        """
        cache_name = sorted(source)+['_']+sorted(target)
        projection = self._get_from_cache(cache_name, 'projection')
        if projection is None:
            source_idx = self.get_source(source, hemisphere)
            target_idx = self.get_target(target, hemisphere)

            self._load_voxel_data()
            projection = self.voxel_array[source_idx, target_idx]
            self.save_to_cache(cache_name, 'projection', projection)

        if projection_mode == 'mean':
            proj = np.mean(projection, axis=0)
        elif projection_mode == 'max':
            proj = np.max(projection, axis=0)
        else:
            raise ValueError(f'Projection mode {projection_mode} not recognized.\n'+
                            'Should be one of: ["mean", "max"].')

        self.projections[name] = proj
        self.get_target_mask(target, hemisphere)
        return proj

    
    def get_mapped_projection(self, source, target, name, **kwargs):
        """
            Gets the spatialised projection intensity from a source to a target, but as 
            a mapped volume instead of a linear array. 

            :param source: str or list of str with acronym of source regions
            :param target: str or list of str with acronym of target regions
            :param name: str, name of the projection

            :return: 3D numpy array with projectino intensity
        """
        projection = self.get_projection(source, target, name, **kwargs)
        mapped_projection = self.tgt_mask.map_masked_to_annotation(projection)
        self.mapped_projections[name] = mapped_projection
        return mapped_projection

    def render_mapped_projection(self, source, target, 
                        std_above_mean_threshold=5,
                        cmap='Greens', alpha=.5,
                        **kwargs):
        """
            Gets the spatialised projection intensity from a source to a target
            and renders it as a vtkplotter lego visualisation.

            :param source: str or list of str with acronym of source regions
            :param target: str or list of str with acronym of target regions
            :param cmap: str with name of colormap to use
            :param alpha: float, transparency
        """
        if not isinstance(source, list): source = [source]
        if not isinstance(target, list): target = [target]
        name = ''.join(source)+'_'.join(target)

        mapped_projection = self.get_mapped_projection(source, target, name, **kwargs)

        vol = Volume(mapped_projection)
        lego = vol.legosurface(vmin=np.mean(mapped_projection)+
                                        std_above_mean_threshold*np.std(mapped_projection), 
                                vmax=np.max(mapped_projection), 
                                cmap=cmap).alpha(alpha).lw(0).scale(100)
        actor = self.scene.add_vtkactor(lego)
        return actor
    
    def render(self):
        """
            Renders the scene associated with the class
        """
        self.scene.render()

