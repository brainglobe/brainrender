from pathlib import Path

from vtkplotter import load

from brainatlas_api.bg_atlas import FishAtlas

import brainrender
from brainrender.atlases.base import Atlas
from brainrender.colors import check_colors
from brainrender.Utils import actors_funcs
from brainrender.Utils.data_io import load_mesh_from_file

class BrainGlobeAtlas(Atlas):
    def __init__(self,  base_dir=None, **kwargs):
        Atlas.__init__(self, base_dir=base_dir, **kwargs)

        

        
    # ---------------------------------------------------------------------------- #
    #                      METHODS SUPPORTING SCENE POPULATION                     #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def _check_valid_region_arg(region):
        """
        Check that the string passed is a valid brain region name.

        :param region: string, acronym of a brain region according to the Allen Brain Atlas.

        """
        if not isinstance(region, int) and not isinstance(region, str):
            raise ValueError("region must be a list, integer or string, not: {}".format(type(region)))
        else:
            return True

    def _get_structure_mesh(self,  acronym,   **kwargs):
        obj_path = self.get_mesh_file_from_acronym(acronym)
        return load_mesh_from_file(obj_path, **kwargs)


            
    def get_brain_regions(self, brain_regions,
                            add_labels=False,
                            colors=None, use_original_color=True, 
                            alpha=None, hemisphere=None, verbose=False, **kwargs):

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
            # Check that the atlas has brain regions data
            if self.structures_acronyms is None:
                print(f"The atlas {self.atlas_name} has no brain regions data")
                return

            # Parse arguments
            if alpha is None:
                alpha = brainrender.DEFAULT_STRUCTURE_ALPHA

            # check that we have a list
            if not isinstance(brain_regions, list):
                brain_regions = [brain_regions]

            # check the colors input is correct
            if colors is not None:
                if isinstance(colors[0], (list, tuple)):
                    if not len(colors) == len(brain_regions): 
                        raise ValueError("when passing colors as a list, the number of colors must match the number of brain regions")
                    for col in colors:
                        if not check_colors(col): raise ValueError("Invalide colors in input: {}".format(col))
                else:
                    if not check_colors(colors): raise ValueError("Invalide colors in input: {}".format(colors))
                    colors = [colors for i in range(len(brain_regions))]

            # loop over all brain regions
            actors = {}
            for i, region in enumerate(brain_regions):
                self._check_valid_region_arg(region)

                if region in self.ignore_regions: continue
                if verbose: print("Rendering: ({})".format(region))

                # get the structure and check if we need to download the object file
                if region not in self.structures_acronyms:
                    print(f"The region {region} doesn't seem to belong to the atlas being used: {self.atlas_name}. Skipping")
                    continue

                # Get path to .obj file
                obj_file = str(self.get_mesh_file_from_acronym(region))

                # check which color to assign to the brain region
                if use_original_color:
                    color = [x/255 for x in self.get_region_color_from_acronym(region)]
                else:
                    if colors is None:
                        color = brainrender.DEFAULT_STRUCTURE_COLOR
                    elif isinstance(colors, list):
                        color = colors[i]
                    else: 
                        color = colors

                # Load the object file as a mesh and store the actor
                if hemisphere is not None:
                    if hemisphere.lower() == "left" or hemisphere.lower() == "right":
                        obj = self.get_region_unilateral(region, hemisphere=hemisphere, color=color, alpha=alpha)
                    else:
                        raise ValueError(f'Invalid hemisphere argument: {hemisphere}')
                else:
                    obj = load(obj_file, c=color, alpha=alpha)

                if obj is not None:
                    actors_funcs.edit_actor(obj, **kwargs)

                    actors[region] = obj
                else:
                    print(f"Something went wrong while loading mesh data for {region}")

            return actors



class BGFishAtlas(BrainGlobeAtlas, FishAtlas):
    atlas_name = "fishatlas"

    def __init__(self, base_dir=None, **kwargs):
        BrainGlobeAtlas.__init__(self, base_dir=base_dir, **kwargs)
        FishAtlas.__init__(self)

        self.meshes_folder = self.root_dir / "meshes"

