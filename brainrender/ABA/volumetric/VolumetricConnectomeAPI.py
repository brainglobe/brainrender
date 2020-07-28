import numpy as np
import os
from pathlib import Path
from vedo import Volume

# TODO see if this can be added to setup.py
try:
    from mcmodels.core import VoxelModelCache, Mask
    from mcmodels.models.voxel.voxel_connectivity_array import (
        VoxelConnectivityArray,
    )
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "To use this functionality you need to install mcmodels "
        + "with: 'pip install git+https://github.com/AllenInstitute/mouse_connectivity_models.git'"
    )

from brainrender.Utils.paths_manager import Paths
from brainrender.scene import Scene
from brainrender.Utils.data_io import (
    connected_to_internet,
    load_npy_from_gz,
    save_npy_to_gz,
)
from brainrender.colors import get_random_colormap


class VolumetricAPI(Paths):
    """
        This class takes care of downloading, analysing and rendering data from:
        "High-resolution data-driven model of the mouse connectome ", Knox et al 2018.
        [https://www.mitpressjournals.org/doi/full/10.1162/netn_a_00066].

        These data can be used to look at spatialised projection strength with sub-region (100um) resolution.
        e.g. to look at where in region B are the projections from region A, you can use this class.

        To download the data, this class uses code from: https://github.com/AllenInstitute/mouse_connectivity_models.
    """

    voxel_size = 100

    projections = {}
    mapped_projections = {}

    hemispheres = dict(left=1, right=2, both=3)

    def __init__(
        self,
        base_dir=None,
        add_root=True,
        use_cache=True,
        scene_kwargs={},
        **kwargs,
    ):
        """
            Initialise the class instance to get a few useful paths and variables. 

            :param base_dir: str, path to base directory in which all of brainrender data are stored. 
                    Pass only if you want to use a different one from what's default.
            :param add_root: bool, if True the root mesh is added to the rendered scene
            :param use_cache: if true data are loaded from a cache to speed things up.
                    Useful to set it to false to help debugging.
            :param scene_kwargs: dict, params passed to the instance of Scene associated with this class
        """
        Paths.__init__(self, base_dir=base_dir, **kwargs)

        # Get MCM cache
        cache_path = (
            Path(self.mouse_connectivity_volumetric)
            / "voxel_model_manifest.json"
        )

        if not cache_path.exists():
            if not connected_to_internet():
                raise ValueError(
                    "The first time you use this class it will need to download some data, but it seems that you're not connected to the internet."
                )
            print(
                "Downloading volumetric data. This will take several minutes but it only needs to be done once."
            )

        self.cache = VoxelModelCache(manifest_file=str(cache_path))
        self.voxel_array = None
        self.target_coords, self.source_coords = None, None

        # Get projection cache paths
        self.data_cache = self.mouse_connectivity_volumetric_cache
        self.data_cache_projections = os.path.join(
            self.data_cache, "projections"
        )
        self.data_cache_targets = os.path.join(self.data_cache, "targets")
        self.data_cache_sources = os.path.join(self.data_cache, "sources")

        for fold in [
            self.data_cache_projections,
            self.data_cache_targets,
            self.data_cache_sources,
        ]:
            if not os.path.isdir(fold):
                os.mkdir(fold)

        # Get structures tree
        self.structure_tree = self.cache.get_structure_tree()

        # Get scene
        self.scene = Scene(add_root=add_root, **scene_kwargs)

        # Other vars
        self.use_cache = use_cache

    def __getattr__(self, attr):
        __dict__ = super(VolumetricAPI, self).__getattribute__("__dict__")
        try:
            return __dict__["scene"].__getattribute__(attr)
        except AttributeError as e:
            raise AttributeError(
                f"Could not attribute {attr} for class VolumetricAPI:\n{e}"
            )

    # ---------------------------------------------------------------------------- #
    #                                     UTILS                                    #
    # ---------------------------------------------------------------------------- #
    # ------------------------- Interaction with mcmodels ------------------------ #

    def _get_structure_id(self, struct):
        " Get the ID of a structure (or list of structures) given it's acronym"
        if not isinstance(struct, (list, tuple)):
            struct = [struct]
        return [
            self.structure_tree.get_structures_by_acronym([s])[0]["id"]
            for s in struct
        ]

    def _load_voxel_data(self):
        "Load the VoxelData array from Knox et al 2018"
        if self.voxel_array is None:
            # Get VoxelArray
            weights_file = os.path.join(
                self.mouse_connectivity_volumetric, "voxel_model", "weights"
            )
            nodes_file = os.path.join(
                self.mouse_connectivity_volumetric, "voxel_model", "nodes"
            )

            # Try to load from numpy
            if os.path.isfile(weights_file + ".npy.gz"):
                weights = load_npy_from_gz(weights_file + ".npy.gz")
                nodes = load_npy_from_gz(nodes_file + ".npy.gz")

                # Create array
                self.voxel_array = VoxelConnectivityArray(weights, nodes)

                # Get target and source masks
                self.source_mask = self.cache.get_source_mask()
                self.target_mask = self.cache.get_target_mask()
            else:
                print("Loading voxel data, might take a few minutes.")
                # load from standard cache
                (
                    self.voxel_array,
                    self.source_mask,
                    self.target_mask,
                ) = self.cache.get_voxel_connectivity_array()

                # save to npy
                save_npy_to_gz(
                    weights_file + ".npy.gz", self.voxel_array.weights
                )
                save_npy_to_gz(nodes_file + ".npy.gz", self.voxel_array.nodes)

    def _get_coordinates_from_voxel_id(self, p0, as_source=True):
        """
            Takes the index of a voxel and returns the 3D coordinates in reference space. 
            The index number should be extracted with either a source_mask or a target_mask.
            If target_mask wa used set as_source as False.

            :param p0: int
        """
        if self.voxel_array is None:
            self._load_voxel_data()

        if as_source:
            return self.source_mask.coordinates[p0] * self.voxel_size
        else:
            return self.target_mask.coordinates[p0] * self.voxel_size

    def _get_mask_coords(self, as_source):
        if as_source:
            if self.source_coords is None:
                coordinates = self.source_mask.coordinates * self.voxel_size
                self.source_coords = coordinates
            else:
                coordinates = self.source_coords
        else:
            if self.target_coords is None:
                coordinates = self.target_mask.coordinates * self.voxel_size
                self.target_coords = coordinates
            else:
                coordinates = self.target_coords
        return coordinates

    def _get_voxel_id_from_coordinates(self, p0, as_source=True):
        if self.voxel_array is None:
            self._load_voxel_data()

        # Get the brain region from the coordinates
        coordinates = self._get_mask_coords(as_source)

        # Get the position of p0 in the coordinates volumetric array
        p0 = np.int64([round(p, -2) for p in p0])

        try:
            x_idx = (np.abs(coordinates[:, 0] - p0[0])).argmin()
            y_idx = (np.abs(coordinates[:, 1] - p0[1])).argmin()
            z_idx = (np.abs(coordinates[:, 2] - p0[2])).argmin()
            p0_idx = [x_idx, y_idx, z_idx]
        except:
            raise ValueError(
                f"Could not find the voxe corresponding to the point given: {p0}"
            )
        return p0_idx[0]

    # ----------------------------------- Cache ---------------------------------- #
    def _get_cache_filename(self, tgt, what):
        """Data are cached according to a naming convention, this function gets the name for an object
        according to the convention"""
        if what == "projection":
            fld = self.data_cache_projections
        elif what == "source":
            fld = self.data_cache_sources
        elif what == "target":
            fld = self.data_cache_targets
        else:
            raise ValueError(
                "Error while getting cached data file name.\n"
                + f"What was {what} but should be projection/source/target/actor."
            )

        name = "".join([str(i) for i in tgt])
        path = os.path.join(fld, name + ".npy.gz")
        return name, path, os.path.isfile(path)

    def _get_from_cache(self, tgt, what):
        """ tries to load objects from cached data, if they exist"""
        if not self.use_cache:
            return None

        name, cache_path, cache_exists = self._get_cache_filename(tgt, what)
        if not cache_exists:
            return None
        else:
            return load_npy_from_gz(cache_path)

    def save_to_cache(self, tgt, what, obj):
        """ Saves data to cache to avoid loading thema again in the future"""
        name, cache_path, _ = self._get_cache_filename(tgt, what)
        save_npy_to_gz(cache_path, obj)

    # ---------------------------------------------------------------------------- #
    #                                 PREPROCESSING                                #
    # ---------------------------------------------------------------------------- #

    # ------------------------- Sources and targets masks ------------------------ #

    def get_source(self, source, hemisphere="both"):
        """
            Loads the mask for a source structure

            :param source: str or list of str with acronym of source regions
            :param hemisphere: str, ['both', 'left', 'right']. Which hemisphere to consider.
        """
        if not isinstance(source, (list, tuple)):
            source = [source]

        self.source = self._get_from_cache(source, "source")
        if self.source is None:
            self._load_voxel_data()
            source_ids = self._get_structure_id(source)

            self.source = self.source_mask.get_structure_indices(
                structure_ids=source_ids,
                hemisphere_id=self.hemispheres[hemisphere],
            )
            self.save_to_cache(source, "source", self.source)
        return self.source

    def get_target_mask(self, target, hemisphere):
        """returns a 'key' array and a mask object
            used to transform projection data from linear arrays to 3D volumes.
        """
        target_ids = self._get_structure_id(target)
        self.tgt_mask = Mask.from_cache(
            self.cache,
            structure_ids=target_ids,
            hemisphere_id=self.hemispheres[hemisphere],
        )

    def get_target(self, target, hemisphere="both"):
        """
            Loads the mask for a target structure.  

            :param target: str or list of str with acronym of target regions
            :param hemisphere: str, ['both', 'left', 'right']. Which hemisphere to consider.
        """
        if not isinstance(target, (list, tuple)):
            target = [target]

        if hemisphere != "both":
            cache_name = target + [hemisphere]
        else:
            cache_name = target

        self.target = self._get_from_cache(cache_name, "target")
        if self.target is None:
            self._load_voxel_data()
            target_ids = self._get_structure_id(target)

            self.target = self.target_mask.get_structure_indices(
                structure_ids=target_ids,
                hemisphere_id=self.hemispheres[hemisphere],
            )
            self.save_to_cache(cache_name, "target", self.target)

        return self.target

    # -------------------------------- Projections ------------------------------- #

    def get_projection(
        self,
        source,
        target,
        name,
        hemisphere="both",
        projection_mode="mean",
        mode="target",
    ):
        """
                Gets the spatialised projection intensity from a source to a target. 

                :param source: str or list of str with acronym of source regions
                :param target: str or list of str with acronym of target regions
                :param name: str, name of the projection
                :param projection_mode: str, if 'mean' the data from different experiments are averaged, 
                                    if 'max' the highest value is taken.
                :param mode: str. If 'target' the spatialised projection strength in the target structures is returned, usefule
                        to see where source projects to in target. Otherwise if 'source' the spatialised projection strength in
                        the source structure is return. Useful to see which part of source projects to target.

                :return: 1D numpy array with mean projection from source to target voxels
        """
        if mode == "target":
            self.get_target_mask(target, hemisphere)
        elif mode == "source":
            self.get_target_mask(source, "right")
        else:
            raise ValueError(
                f"Invalide mode: {mode}. Should be either source or target."
            )

        cache_name = (
            sorted(source)
            + ["_"]
            + sorted(target)
            + [f"_{projection_mode}_{mode}"]
        )
        if hemisphere != "both":
            cache_name += [hemisphere]

        proj = self._get_from_cache(cache_name, "projection")
        if proj is None:
            source_idx = self.get_source(source, hemisphere)
            target_idx = self.get_target(target, hemisphere)

            self._load_voxel_data()
            projection = self.voxel_array[source_idx, target_idx]

            if mode == "target":
                axis = 0
            elif mode == "source":
                axis = 1
            else:
                raise ValueError(
                    f"Invalide mode: {mode}. Should be either source or target."
                )

            if projection_mode == "mean":
                proj = np.mean(projection, axis=axis)
            elif projection_mode == "max":
                proj = np.max(projection, axis=axis)
            else:
                raise ValueError(
                    f"Projection mode {projection_mode} not recognized.\n"
                    + 'Should be one of: ["mean", "max"].'
                )

            # Save to cache
            self.save_to_cache(cache_name, "projection", proj)
        self.projections[name] = proj
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

    def get_mapped_projection_to_point(
        self, p0, restrict_to=None, restrict_to_hemisphere="both"
    ):
        """
            Gets projection intensity from all voxels to the voxel corresponding to a point of interest
        """
        cache_name = f"proj_to_{p0[0]}_{p0[1]}_{p0[1]}"
        if restrict_to is not None:
            cache_name += f"_{restrict_to}"

        proj = self._get_from_cache(cache_name, "projection")

        if proj is None:
            p0idx = self._get_voxel_id_from_coordinates(p0, as_source=False)

            if restrict_to is not None:
                source_idx = self.get_source(
                    restrict_to, restrict_to_hemisphere
                )
                proj = self.voxel_array[source_idx, p0idx]

                self.get_target_mask(restrict_to, restrict_to_hemisphere)
                mapped_projection = self.tgt_mask.map_masked_to_annotation(
                    proj
                )
            else:
                proj = self.voxel_array[:, p0idx]
                mapped_projection = self.source_mask.map_masked_to_annotation(
                    proj
                )
            self.save_to_cache(cache_name, "projection", mapped_projection)

            return mapped_projection
        else:
            return proj

    def get_mapped_projection_from_point(
        self, p0, restrict_to=None, restrict_to_hemisphere="both"
    ):
        """
            Gets projection intensity from all voxels to the voxel corresponding to a point of interest
        """
        if self.get_hemispere_from_point(p0) == "left":
            raise ValueError(
                f"The point passed [{p0}] is in the left hemisphere,"
                + ' but "projection from point" only works from the right hemisphere.'
            )

        cache_name = f"proj_from_{p0[0]}_{p0[1]}_{p0[1]}"
        if restrict_to is not None:
            cache_name += f"_{restrict_to}"

        proj = self._get_from_cache(cache_name, "projection")

        if proj is None:
            p0idx = self._get_voxel_id_from_coordinates(p0, as_source=True)

            if restrict_to is not None:
                target_idx = self.get_target(
                    restrict_to, restrict_to_hemisphere
                )
                proj = self.voxel_array[p0idx, target_idx]

                self.get_target_mask(restrict_to, restrict_to_hemisphere)
                mapped_projection = self.tgt_mask.map_masked_to_annotation(
                    proj
                )
            else:
                proj = self.voxel_array[p0idx, :]
                mapped_projection = self.target_mask.map_masked_to_annotation(
                    proj
                )
            self.save_to_cache(cache_name, "projection", mapped_projection)

            return mapped_projection
        else:
            return proj

    # ---------------------------------------------------------------------------- #
    #                                   RENDERING                                  #
    # ---------------------------------------------------------------------------- #
    def add_mapped_projection(
        self,
        source,
        target,
        actor_kwargs={},
        render_source_region=False,
        render_target_region=False,
        regions_kwargs={},
        **kwargs,
    ):
        """
            Gets the spatialised projection intensity from a source to a target
            and renders it as a vedo lego visualisation.

            :param source: str or list of str with acronym of source regions
            :param target: str or list of str with acronym of target regions
            :param render_source_region: bool, if true a wireframe mesh of source regions is rendered
            :param render_target_region: bool, if true a wireframe mesh of target regions is rendered
            :param regions_kwargs: pass options to specify how brain regions should look like
            :param kwargs: kwargs can be used to control how the rendered object looks like. 
                    Look at the arguments of 'add_volume' to see what arguments are available. 
        """
        # Get projection data
        if not isinstance(source, list):
            source = [source]
        if not isinstance(target, list):
            target = [target]
        name = "".join(source) + "_".join(target)
        mapped_projection = self.get_mapped_projection(
            source, target, name, **kwargs
        )
        lego_actor = self.add_volume(mapped_projection, **actor_kwargs)

        # Render relevant regions meshes
        if render_source_region or render_target_region:
            wireframe = regions_kwargs.pop("wireframe", True)
            use_original_color = regions_kwargs.pop("use_original_color", True)

            if render_source_region:
                self.scene.add_brain_regions(
                    source,
                    use_original_color=use_original_color,
                    wireframe=wireframe,
                    **regions_kwargs,
                )
            if render_target_region:
                self.scene.add_brain_regions(
                    target,
                    use_original_color=use_original_color,
                    wireframe=wireframe,
                    **regions_kwargs,
                )
        return lego_actor

    def add_mapped_projection_to_point(
        self,
        p0,
        show_point=True,
        show_point_region=False,
        show_crosshair=True,
        crosshair_kwargs={},
        point_region_kwargs={},
        point_kwargs={},
        from_point=False,
        **kwargs,
    ):
        if not isinstance(p0, (list, tuple, np.ndarray)):
            raise ValueError(
                "point passed should be a list or a 1d array, not: {p0}"
            )

        restrict_to = kwargs.pop("restrict_to", None)
        restrict_to_hemisphere = kwargs.pop("restrict_to_hemisphere", "both")
        if not from_point:
            projection = self.get_mapped_projection_to_point(
                p0,
                restrict_to=restrict_to,
                restrict_to_hemisphere=restrict_to_hemisphere,
            )
        else:
            projection = self.get_mapped_projection_from_point(
                p0,
                restrict_to=restrict_to,
                restrict_to_hemisphere=restrict_to_hemisphere,
            )

        lego_actor = self.add_volume(projection, **kwargs)

        if show_point:
            color = point_kwargs.pop("color", "salmon")
            radius = point_kwargs.pop("radius", 50)
            alpha = point_kwargs.pop("alpha", 1)
            if not show_crosshair:
                self.scene.add_sphere_at_point(
                    p0, color=color, radius=radius, alpha=alpha, **point_kwargs
                )
            else:
                ml = crosshair_kwargs.pop("ml", True)
                dv = crosshair_kwargs.pop("dv", True)
                ap = crosshair_kwargs.pop("ap", True)
                self.scene.add_crosshair_at_point(
                    p0,
                    ml=ml,
                    dv=dv,
                    ap=ap,
                    line_kwargs=crosshair_kwargs,
                    point_kwargs={
                        "color": color,
                        "radius": radius,
                        "alpha": alpha,
                    },
                )

        if show_point_region:
            use_original_color = point_region_kwargs.pop(
                "use_original_color", False
            )
            alpha = point_region_kwargs.pop("alpha", 0.3)
            region = self.scene.atlas.structure_from_coords(p0)
            self.scene.add_brain_regions(
                [region],
                use_original_color=use_original_color,
                alpha=alpha,
                **point_region_kwargs,
            )

        return lego_actor

    def add_mapped_projection_from_point(self, *args, **kwargs):
        return self.add_mapped_projection_to_point(
            *args, **kwargs, from_point=True
        )

    def add_volume(
        self, volume, cmap="afmhot_r", alpha=1, add_colorbar=True, **kwargs
    ):
        """
            Renders intensitdata from a 3D numpy array as a lego volumetric actor. 

            :param volume: np 3D array with number of dimensions = those of the 100um reference space. 
            :param cmap: str with name of colormap to use
            :param alpha: float, transparency
          
            :param add_colorbar: if True a colorbar is added to show the values of the colormap
        """
        # Parse kwargs
        line_width = kwargs.pop("line_width", 1)
        if cmap == "random" or not cmap or cmap is None:
            cmap = get_random_colormap()

        # Get vmin and vmax threshold for visualisation
        vmin = kwargs.pop("vmin", 0.000001)
        vmax = kwargs.pop("vmax", np.nanmax(volume))

        # Check values
        if np.max(volume) > vmax:
            print(
                "While rendering mapped projection some of the values are above the vmax threshold."
                + "They will not be displayed."
                + f" vmax was {vmax} but found value {round(np.max(volume), 5)}."
            )

        if vmin > vmax:
            raise ValueError(
                f"The vmin threhsold [{vmin}] cannot be larger than the vmax threshold [{vmax}"
            )
        if vmin < 0:
            vmin = 0

        # Get 'lego' actor
        vol = Volume(volume)
        lego = vol.legosurface(vmin=vmin, vmax=vmax, cmap=cmap)

        # Scale and color actor
        lego.alpha(alpha).lw(line_width).scale(self.voxel_size)
        lego.cmap = cmap

        # Add colorbar
        if add_colorbar:
            lego.addScalarBar(
                vmin=vmin,
                vmax=vmax,
                horizontal=1,
                c="k",
                pos=(0.05, 0.05),
                titleFontSize=40,
            )

        # Add to scene
        actor = self.scene.add_actor(lego)
        return actor
