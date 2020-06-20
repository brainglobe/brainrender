import pandas as pd
import numpy as np
from vedo import load

import brainrender
from brainrender.atlases.base import Atlas
from brainrender.colors import check_colors
from brainrender.Utils import actors_funcs
from brainrender.Utils.data_io import load_mesh_from_file
from brainrender.Utils.data_manipulation import return_list_smart


class BrainGlobeAtlasBase(Atlas):
    def __init__(self, base_dir=None, **kwargs):
        Atlas.__init__(self, base_dir=base_dir, **kwargs)

    # ---------------------------------------------------------------------------- #
    #                      METHODS SUPPORTING SCENE POPULATION                     #
    # ---------------------------------------------------------------------------- #
    def _get_structure_mesh(self, acronym, **kwargs):
        obj_path = self._get_from_structure(acronym, "mesh_filename")
        return load_mesh_from_file(obj_path, **kwargs)

    def get_brain_regions(
        self,
        brain_regions,
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

        # check that we have a list
        if not isinstance(brain_regions, list):
            brain_regions = [brain_regions]

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
            if region in self.ignore_regions:
                continue
            if verbose:
                print("Rendering: ({})".format(region))

            # get the structure and check if we need to download the object file
            if region not in self.lookup.acronym.values:
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
                obj = load(obj_file, c=color, alpha=alpha)

            if obj is not None:
                actors_funcs.edit_actor(obj, **kwargs)

                actors[region] = obj
            else:
                print(
                    f"Something went wrong while loading mesh data for {region}, skipping."
                )

        return actors

    # ---------------------------------------------------------------------------- #
    #                                     UTILS                                    #
    # ---------------------------------------------------------------------------- #

    # ! most of this code should be moved to brainglobe

    def get_structure_ancestors(
        self, regions, ancestors=True, descendants=False
    ):
        """
        Get's the ancestors of the region(s) passed as arguments

        :param regions: str, list of str with acronums of regions of interest
        :param ancestors: if True, returns the ancestors of the region  (Default value = True)
        :param descendants: if True, returns the descendants of the region (Default value = False)

        """

        if not isinstance(regions, list):
            struct_id = self.structure_tree.get_structures_by_acronym(
                [regions]
            )[0]["id"]
            return pd.DataFrame(
                self.tree_search.get_tree(
                    "Structure",
                    struct_id,
                    ancestors=ancestors,
                    descendants=descendants,
                )
            )
        else:
            ancestors = []
            for region in regions:
                struct_id = self.structure_tree.get_structures_by_acronym(
                    [region]
                )[0]["id"]
                ancestors.append(
                    pd.DataFrame(
                        self.tree_search.get_tree(
                            "Structure",
                            struct_id,
                            ancestors=ancestors,
                            descendants=descendants,
                        )
                    )
                )
            return ancestors

    def get_structure_descendants(self, regions):
        return self.get_structure_ancestors(
            regions, ancestors=False, descendants=True
        )

    def get_structure_parent(self, acronyms):
        """
        Gets the parent of a brain region (or list of regions) from the hierarchical structure of the
        Allen Brain Atals.

        :param acronyms: list of acronyms of brain regions.

        """
        if not isinstance(acronyms, list):
            s = self.structure_tree.get_structures_by_acronym([acronyms])[0]
            if s["id"] in self.lookup.id.values:
                return s
            else:
                return self.get_structure_ancestors(s["acronym"]).iloc[-1]
        else:
            parents = []
            for region in acronyms:
                s = self.structure_tree.get_structures_by_acronym(acronyms)[0]

                if s["id"] in self.lookup.id.values:
                    parents.append(s)
                parents.append(
                    self.get_structure_ancestors(s["acronym"]).iloc[-1]
                )
            return parents

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
        right = bilateralmesh.cutWithPlane(origin=com, normal=(0, 0, 1))

        # left is the mirror right # WIP
        com = self.get_region_CenterOfMass("root", unilateral=False)[2]
        left = actors_funcs.mirror_actor_at_point(right.clone(), com, axis="x")

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


class BrainGlobeAtlas(BrainGlobeAtlasBase):
    default_camera = None

    def __init__(self, atlas):
        BrainGlobeAtlasBase.__init__(self)

        atlas = atlas()  # make sure data is downloaded

        for name, attr in atlas.__dict__.items():
            self.__setattr__(name, attr)

        for attr in dir(atlas):
            if attr.startswith("__"):
                continue
            try:
                self.__setattr__(attr, atlas.__getattribute__(attr))
            except AttributeError:
                pass

        self.meshes_folder = self.root_dir / "meshes"
