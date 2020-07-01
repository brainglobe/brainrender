from vedo import Mesh, Plane
import numpy as np
import pandas as pd

import brainrender
from brainrender.Utils.data_io import load_mesh_from_file
from brainrender.Utils import actors_funcs
from brainrender.Utils.data_manipulation import (
    return_list_smart,
    return_dict_smart,
)
from brainrender.colors import check_colors


class Base:
    default_camera = None

    def __init__(self,):
        return

    # ---------------------------------------------------------------------------- #
    #                                    METHODS                                   #
    # ---------------------------------------------------------------------------- #
    # ---------------------------------- Planes ---------------------------------- #
    # functions to create oriented planes that can be used to slice actors etc
    def get_plane_at_point(
        self, pos, norm, sx, sy, color="lightgray", alpha=0.25, **kwargs
    ):
        """ 
            Returns a plane going through a point at pos, oriented 
            orthogonally to the vector norm and of width and height
            sx, sy. 

            :param pos: 3-tuple or list with x,y,z, coords of point the plane goes through
            :param sx, sy: int, width and height of the plane
            :param norm: 3-tuple or list with 3d vector the plane is orthogonal to
            :param color, alpha: plane color and transparency
        """
        plane = Plane(pos=pos, normal=norm, sx=sx, sy=sy, c=color, alpha=alpha)
        return plane

    def get_sagittal_plane(self, pos=None, **kwargs):
        """
            Creates a Plane actor centered at the midpoint of root (or a user given locatin)
            and oriented along the sagittal axis

            :param pos: if not None, passe a list of 3 xyz defining the position of the 
                            point the plane goes through.
        """
        if pos is None:
            pos = self._root_midpoint
            if pos[0] is None:
                raise ValueError(
                    "The atlases _root_midpoint attribute is not specified"
                )
        elif not isinstance(pos, (list, tuple)) or not len(pos) == 3:
            raise ValueError(f"Invalid pos argument: {pos}")

        norm = self._planes_norms["sagittal"]
        sx = float(np.diff(self._root_bounds[0]))
        sy = float(np.diff(self._root_bounds[1]))

        sx += sx / 5
        sy += sy / 5
        sag_plane = self.get_plane_at_point(pos, norm, sx, sy, **kwargs)

        return sag_plane

    def get_horizontal_plane(self, pos=None, **kwargs):
        """
            Creates a Plane actor centered at the midpoint of root (or a user given locatin)
            and oriented along the horizontal axis

            :param pos: if not None, passe a list of 3 xyz defining the position of the 
                            point the plane goes through.
        """
        if pos is None:
            pos = self._root_midpoint
            if pos[0] is None:
                raise ValueError(
                    "The atlases _root_midpoint attribute is not specified"
                )
        elif not isinstance(pos, (list, tuple)) or not len(pos) == 3:
            raise ValueError(f"Invalid pos argument: {pos}")

        norm = self._planes_norms["horizontal"]
        sx = float(np.diff(self._root_bounds[2]))
        sy = float(np.diff(self._root_bounds[0]))

        sx += sx / 5
        sy += sy / 5
        hor_plane = self.get_plane_at_point(pos, norm, sx, sy, **kwargs)

        return hor_plane

    def get_coronal_plane(self, pos=None, **kwargs):
        """
            Creates a Plane actor centered at the midpoint of root (or a user given locatin)
            and oriented along the coronal axis

            :param pos: if not None, passe a list of 3 xyz defining the position of the 
                            point the plane goes through.
        """
        if pos is None:
            pos = self._root_midpoint
            if pos[0] is None:
                raise ValueError(
                    "The atlases _root_midpoint attribute is not specified"
                )
        elif not isinstance(pos, (list, tuple)) or not len(pos) == 3:
            raise ValueError(f"Invalid pos argument: {pos}")

        norm = self._planes_norms["coronal"]
        sx = float(np.diff(self._root_bounds[2]))
        sy = float(np.diff(self._root_bounds[1]))

        sx += sx / 5
        sy += sy / 5
        cor_plane = self.get_plane_at_point(pos, norm, sx, sy, **kwargs)

        return cor_plane

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
            if s["id"] in self.lookup_df.id.values:
                return s
            else:
                return self.get_structure_ancestors(s["acronym"]).iloc[-1]
        else:
            parents = []
            for region in acronyms:
                s = self.structure_tree.get_structures_by_acronym(acronyms)[0]

                if s["id"] in self.lookup_df.id.values:
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
