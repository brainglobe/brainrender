from vedo import Mesh, Plane, merge
from morphapi.morphology.morphology import Neuron
import numpy as np
import os
from bg_atlasapi.bg_atlas import BrainGlobeAtlas
from pyinspect.classes import Enhanced

import brainrender
from brainrender.Utils.paths_manager import Paths
from brainrender.atlases.aba import ABA
from brainrender.Utils.data_io import load_mesh_from_file
from brainrender.Utils import actors_funcs
from brainrender.Utils.data_manipulation import (
    return_list_smart,
    return_dict_smart,
    flatten,
)
from brainrender.colors import check_colors
from brainrender.Utils.atlases_utils import parse_neurons_colors
from brainrender.morphology.utils import get_neuron_actors_with_morphapi


class Atlas(BrainGlobeAtlas, Paths, ABA, Enhanced):
    default_camera = None

    def __init__(self, atlas_name, *args, base_dir=None, **kwargs):
        # Create brainglobe atlas
        BrainGlobeAtlas.__init__(
            self, *args, atlas_name=atlas_name, print_authors=False, **kwargs
        )

        # Add brainrender paths
        Paths.__init__(self, base_dir=base_dir, **kwargs)

        Enhanced.__init__(self)

        # If it's a mouse atlas, add extra functionality
        if "Mus musculus" == self.metadata["species"]:
            ABA.__init__(self)

    # ---------------------------------------------------------------------------- #
    #                                    METHODS                                   #
    # ---------------------------------------------------------------------------- #
    # ---------------------------------- Planes ---------------------------------- #
    # functions to create oriented planes that can be used to slice actors etc
    def get_plane_at_point(
        self,
        pos=None,
        norm=None,
        plane=None,
        sx=None,
        sy=None,
        color="lightgray",
        alpha=0.25,
        **kwargs,
    ):
        """ 
            Returns a plane going through a point at pos, oriented 
            orthogonally to the vector norm and of width and height
            sx, sy. 

            :param pos: 3-tuple or list with x,y,z, coords of point the plane goes through
            :param norm: 3-tuple with plane's normal vector (optional)
            :param sx, sy: int, width and height of the plane
            :param plane: "sagittal", "horizontal", or "frontal"
            :param color, alpha: plane color and transparency
        """
        axes_pairs = dict(sagittal=(0, 1), horizontal=(2, 0), frontal=(2, 1))

        # Get position
        if pos is None:
            pos = self._root_midpoint
        elif not isinstance(pos, (list, tuple)) or not len(pos) == 3:
            raise ValueError(f"Invalid pos argument: {pos}")

        # Get normal if one is not given
        if norm is None:
            try:
                norm = self.space.plane_normals[plane]
            except KeyError:
                raise ValueError(
                    f"Could not find normals for plane {plane}. Atlas space {self.space} provides these normals: {self.spacel.plane_normals}"
                )

        # Get plane width and height
        idx_pair = (
            axes_pairs[plane]
            if plane is not None
            else axes_pairs["horizontal"]
        )
        wh = [float(np.diff(self._root_bounds[i])) * 1.2 for i in idx_pair]
        if sx is None:
            sx = wh[0]
        if sy is None:
            sy = wh[1]

        # return plane
        return Plane(pos=pos, normal=norm, sx=sx, sy=sy, c=color, alpha=alpha)

    # ----------------------------------- Misc ----------------------------------- #
    def get_region_CenterOfMass(
        self, regions, unilateral=True, hemisphere="right"
    ):
        """
        Get the center of mass of the 3d mesh of one or multiple brain regions.

        :param regions: str, list of brain regions acronyms
        :param unilateral: bool, if True, the CoM is relative to one hemisphere (Default value = True)
        :param hemisphere: str, if unilteral=True, specifies which hemisphere to use ['left' or 'right'] (Default value = "right")
        :returns: coms = {list, dict} -- [if only one regions is passed, then just returns the CoM coordinates for that region.
                                If a list is passed then a dictionary is returned. ]
        """

        if not isinstance(regions, list):
            regions = [regions]

        coms = {}
        for region in regions:
            # Check if input is an actor or if we need to load one
            if isinstance(region, Mesh):
                mesh = region
            else:
                # load mesh corresponding to brain region
                if unilateral:
                    mesh = self.get_region_unilateral(
                        region, hemisphere="left"
                    )
                else:
                    mesh = self._get_structure_mesh(region)
            com = mesh.centerOfMass()

            #  if using right hemisphere, mirror COM
            if unilateral and hemisphere.lower() == "right":
                com = self.mirror_point_across_hemispheres(com)

            coms[region] = com

        # return data
        return return_dict_smart(coms)

    # ---------------------------------------------------------------------------- #
    #                      METHODS SUPPORTING SCENE POPULATION                     #
    # ---------------------------------------------------------------------------- #
    def _get_structure_mesh(self, acronym, **kwargs):
        obj_path = self._get_from_structure(acronym, "mesh_filename")
        return load_mesh_from_file(obj_path, **kwargs)

    def get_brain_regions(
        self,
        *brain_regions,
        add_labels=False,
        colors=None,
        use_original_color=True,
        alpha=None,
        hemisphere=None,
        verbose=False,
        **kwargs,
    ):

        """
                Gets brain regions meshes for rendering
                Many parameters can be passed to specify how the regions should be rendered.
                To treat a subset of the rendered regions, specify which regions are VIP. 
                Use the kwargs to specify more detailes on how the regins should be rendered (e.g. wireframe look)

                :param brain_regions: str list of acronyms of brain regions
                :param colors: str, color of rendered brian regions (Default value = None)
                :param use_original_color: bool, if True, the allen's default color for the region is used.  (Default value = False)
                :param alpha: float, transparency of the rendered brain regions (Default value = None)
                :param hemisphere: str (Default value = None)
                :param add_labels: bool (default False). If true a label is added to each regions' actor. The label is visible when hovering the mouse over the actor
                :param **kwargs: used to determine a bunch of thigs, including the look and location of lables from scene.add_labels
            """
        # Parse arguments
        if alpha is None:
            alpha = brainrender.DEFAULT_STRUCTURE_ALPHA

        # Flatten brain regions argument
        if isinstance(brain_regions[0], list):
            brain_regions = flatten(brain_regions)

        # check the colors input is correct
        if colors is not None:
            if isinstance(colors, (list, tuple)):
                if not len(colors) == len(brain_regions):
                    raise ValueError(
                        "when passing colors as a list, the number of colors must match the number of brain regions"
                    )
                for col in colors:
                    if not check_colors(col):
                        raise ValueError(
                            "Invalide colors in input: {}".format(col)
                        )
            else:
                if not check_colors(colors):
                    raise ValueError(
                        "Invalide colors in input: {}".format(colors)
                    )
                colors = [colors for i in range(len(brain_regions))]

        # loop over all brain regions
        actors = {}
        for i, region in enumerate(brain_regions):
            if verbose:
                print("Rendering: ({})".format(region))

            # get the structure and check if we need to download the object file
            if region not in self.lookup_df.acronym.values:
                print(
                    f"The region {region} doesn't seem to belong to the atlas being used: {self.atlas_name}. Skipping"
                )
                continue

            # Get path to .obj file
            obj_file = str(self.meshfile_from_structure(region))

            # check which color to assign to the brain region
            if use_original_color:
                color = [
                    x / 255
                    for x in self._get_from_structure(region, "rgb_triplet")
                ]
            else:
                if colors is None:
                    color = brainrender.DEFAULT_STRUCTURE_COLOR
                elif isinstance(colors, list):
                    color = colors[i]
                else:
                    color = colors

            # Load the object file as a mesh and store the actor
            if hemisphere is not None:
                if (
                    hemisphere.lower() == "left"
                    or hemisphere.lower() == "right"
                ):
                    obj = self.get_region_unilateral(
                        region, hemisphere=hemisphere, color=color, alpha=alpha
                    )
                else:
                    raise ValueError(
                        f"Invalid hemisphere argument: {hemisphere}"
                    )
            else:
                obj = load_mesh_from_file(obj_file, color=color, alpha=alpha)

            if obj is not None:
                actors_funcs.edit_actor(obj, **kwargs)
                actors[region] = obj
            else:
                print(
                    f"Something went wrong while loading mesh data for {region}, skipping."
                )

        return actors

    def get_neurons(
        self,
        neurons,
        color=None,
        display_axon=True,
        display_dendrites=True,
        alpha=1,
        neurite_radius=None,
        soma_radius=None,
        use_cache=True,
    ):
        """
        Gets rendered morphological data of neurons reconstructions
        Accepts neurons argument as:
            - file(s) with morphological data
            - vedo mesh actor(s) of entire neurons reconstructions
            - dictionary or list of dictionary with actors for different neuron parts

        :param neurons: str, list, dict. File(s) with neurons data or list of rendered neurons.
        :param display_axon, display_dendrites: if set to False the corresponding neurite is not rendered
        :param color: default None. Can be:
                - None: each neuron is given a random color
                - color: rbg, hex etc. If a single color is passed all neurons will have that color
                - cmap: str with name of a colormap: neurons are colored based on their sequential order and cmap
                - dict: a dictionary specifying a color for soma, dendrites and axon actors, will be the same for all neurons
                - list: a list of length = number of neurons with either a single color for each neuron
                        or a dictionary of colors for each neuron
        :param alpha: float in range 0,1. Neurons transparency
        :param neurite_radius: float > 0 , radius of tube actor representing neurites
        :param use_cache: bool, if True a cache is used to avoid having to crate a neuron's mesh anew, otherwise a new mesh is created
        """

        if not isinstance(neurons, (list, tuple)):
            neurons = [neurons]

        # ---------------------------------- Render ---------------------------------- #
        _neurons_actors = []
        for neuron in neurons:
            neuron_actors = {"soma": None, "dendrites": None, "axon": None}

            # Deal with neuron as filepath
            if isinstance(neuron, str):
                if os.path.isfile(neuron):
                    if neuron.endswith(".swc"):
                        neuron_actors, _ = get_neuron_actors_with_morphapi(
                            swcfile=neuron,
                            neurite_radius=neurite_radius,
                            soma_radius=soma_radius,
                            use_cache=use_cache,
                        )
                    else:
                        raise NotImplementedError(
                            "Currently we can only parse morphological reconstructions from swc files"
                        )
                else:
                    raise ValueError(
                        f"Passed neruon {neuron} is not a valid input. Maybe the file doesn't exist?"
                    )

            # Deal with neuron as single actor
            elif isinstance(neuron, Mesh):
                # A single actor was passed, maybe it's the entire neuron
                neuron_actors["soma"] = neuron  # store it as soma
                pass

            # Deal with neuron as dictionary of actor
            elif isinstance(neuron, dict):
                neuron_actors["soma"] = neuron.pop("soma", None)
                neuron_actors["axon"] = neuron.pop("axon", None)

                # Get dendrites actors
                if (
                    "apical_dendrites" in neuron.keys()
                    or "basal_dendrites" in neuron.keys()
                ):
                    if "apical_dendrites" not in neuron.keys():
                        neuron_actors["dendrites"] = neuron["basal_dendrites"]
                    elif "basal_dendrites" not in neuron.keys():
                        neuron_actors["dendrites"] = neuron["apical_dendrites"]
                    else:
                        neuron_actors["dendrites"] = merge(
                            neuron["apical_dendrites"],
                            neuron["basal_dendrites"],
                        )
                else:
                    neuron_actors["dendrites"] = neuron.pop("dendrites", None)

            # Deal with neuron as instance of Neuron from morphapi
            elif isinstance(neuron, Neuron):
                neuron_actors, _ = get_neuron_actors_with_morphapi(
                    neuron=neuron,
                    neurite_radius=neurite_radius,
                    use_cache=use_cache,
                )
            # Deal with other inputs
            else:
                raise ValueError(
                    f"Passed neuron {neuron} is not a valid input"
                )

            # Check that we don't have anything weird in neuron_actors
            for key, act in neuron_actors.items():
                if act is not None:
                    if not isinstance(act, Mesh):
                        raise ValueError(
                            f"Neuron actor {key} is {type(act)} but should be a vedo Mesh. Not: {act}"
                        )

            if not display_axon:
                neuron_actors["axon"] = None
            if not display_dendrites:
                neuron_actors["dendrites"] = None
            _neurons_actors.append(neuron_actors)

        # Color actors
        colors = parse_neurons_colors(neurons, color)
        for n, neuron in enumerate(_neurons_actors):
            if neuron["axon"] is not None:
                neuron["axon"].c(colors["axon"][n])
                neuron["axon"].name = "neuron-axon"
            if neuron["soma"] is not None:
                neuron["soma"].c(colors["soma"][n])
                neuron["soma"].name = "neuron-soma"
            if neuron["dendrites"] is not None:
                neuron["dendrites"].c(colors["dendrites"][n])
                neuron["dendrites"].name = "neuron-dendrites"

        # Return
        return return_list_smart(_neurons_actors), None

    # ---------------------------------------------------------------------------- #
    #                                     UTILS                                    #
    # ---------------------------------------------------------------------------- #

    def get_region_unilateral(
        self, region, hemisphere="both", color=None, alpha=None
    ):
        """
        Regions meshes are loaded with both hemispheres' meshes by default.
        This function splits them in two.

        :param region: str, actors of brain region
        :param hemisphere: str, which hemisphere to return ['left', 'right' or 'both'] (Default value = "both")
        :param color: color of each side's mesh. (Default value = None)
        :param alpha: transparency of each side's mesh.  (Default value = None)

        """
        if color is None:
            color = brainrender.ROOT_COLOR
        if alpha is None:
            alpha = brainrender.ROOT_ALPHA
        bilateralmesh = self._get_structure_mesh(region, c=color, alpha=alpha)

        if bilateralmesh is None:
            print(f"Failed to get mesh for {region}, returning None")
            return None

        com = (
            bilateralmesh.centerOfMass()
        )  # this will always give a point that is on the midline
        right = bilateralmesh.cutWithPlane(origin=com, normal=(0, 0, 1)).c(
            color
        )

        # left is the mirror right # WIP
        com = self.get_region_CenterOfMass("root", unilateral=False)[2]
        left = actors_funcs.mirror_actor_at_point(
            right.clone(), com, axis="x"
        ).c(color)

        if hemisphere == "both":
            return left, right
        elif hemisphere == "left":
            return left
        else:
            return right

    def mirror_point_across_hemispheres(self, point):
        delta = point[2] - self._root_midpoint[2]
        point[2] = self._root_midpoint[2] - delta
        return point

    def get_colors_from_coordinates(self, p0):
        """
            Given a point or a list of points returns a list of colors where
            each item is the color of the brain region each point is in
        """
        if isinstance(p0[0], (float, int)):
            p0 = [p0]

        resolution = int(self.metadata["resolution"][0])

        colors = []
        for point in p0:
            point = np.round(np.array(point) / resolution).astype(int)
            try:
                struct = self.structure_from_coords(point, as_acronym=True)
            except KeyError:  # couldn't find any region
                struct = "root"
            colors.append(self._get_from_structure(struct, "rgb_triplet"))
        return return_list_smart(colors)
