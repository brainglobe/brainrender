import os
import numpy as np
import pandas as pd
from tqdm import tqdm

from vtkplotter import shapes

from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
from allensdk.api.queries.ontologies_api import OntologiesApi
from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
from allensdk.api.queries.tree_search_api import TreeSearchApi
from allensdk.core.reference_space_cache import ReferenceSpaceCache

from brainatlas_api.bg_atlas import AllenBrain25Um

import brainrender
from brainrender.atlases.brainglobe import BrainGlobeAtlas
from brainrender.colors import check_colors, get_random_colors
from brainrender.morphology.utils import (
    edit_neurons,
    get_neuron_actors_with_morphapi,
)
from brainrender.Utils.ABA.aba_utils import (
    parse_streamline,
    download_streamlines,
    experiments_source_search,
)
from brainrender.Utils.ABA.aba_utils import (
    parse_neurons_colors,
    parse_tractography_colors,
)
from brainrender.Utils.data_manipulation import (
    return_list_smart,
    is_any_item_in_list,
)
from brainrender.Utils import actors_funcs


class ABA(BrainGlobeAtlas):
    """
        This class augments the functionality of
        BrainGlobeAtlas with methods specific to the Allen
        Mouse Brain atlas and necessary to populate scenes in 
        brainrender. These include stuff like fetching streamlines
        and neuronal morphology data. 
    """

    atlas_name = "ABA"

    excluded_regions = ["fiber tracts"]

    # Used for streamlines
    base_url = "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_NNN.json.gz"

    def __init__(self, base_dir=None, **kwargs):
        BrainGlobeAtlas.__init__(self, base_dir=base_dir, **kwargs)

        # get mouse connectivity cache and structure tree
        self.mcc = MouseConnectivityCache(
            manifest_file=os.path.join(
                self.mouse_connectivity_cache, "manifest.json"
            )
        )
        self.structure_tree = self.mcc.get_structure_tree()

        # get ontologies API and brain structures sets
        self.oapi = OntologiesApi()

        # get reference space
        self.space = ReferenceSpaceApi()
        self.spacecache = ReferenceSpaceCache(
            manifest=os.path.join(
                self.annotated_volume_fld, "manifest.json"
            ),  # downloaded files are stored relative to here
            resolution=self.resolution,
            reference_space_key="annotation/ccf_2017",  # use the latest version of the CCF
        )
        self.annotated_volume, _ = self.spacecache.get_annotation_volume()

        # mouse connectivity API [used for tractography]
        self.mca = MouseConnectivityApi()

        # Get tree search api
        self.tree_search = TreeSearchApi()

    # ------------------------- Scene population methods ------------------------- #
    def get_neurons(
        self,
        neurons,
        color=None,
        display_axon=True,
        display_dendrites=True,
        alpha=1,
        neurite_radius=None,
    ):
        """
        Gets rendered morphological data of neurons reconstructions downloaded from the
        Mouse Light project at Janelia (or other sources). 
        Accepts neurons argument as:
            - file(s) with morphological data
            - vtkplotter mesh actor(s) of entire neurons reconstructions
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
                            swcfile=neuron, neurite_radius=neurite_radius
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
            elif isinstance(neuron, Actor):
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
                        neuron_ctors["dendrites"] = merge(
                            neuron["apical_dendrites"],
                            neuron["basal_dendrites"],
                        )
                else:
                    neuron_actors["dendrites"] = neuron.pop("dendrites", None)

            # Deal with neuron as instance of Neuron from morphapi
            elif isinstance(neuron, Neuron):
                neuron_actors, _ = get_neuron_actors_with_morphapi(
                    neuron=neuron
                )
            # Deal with other inputs
            else:
                raise ValueError(
                    f"Passed neuron {neuron} is not a valid input"
                )

            # Check that we don't have anything weird in neuron_actors
            for key, act in neuron_actors.items():
                if act is not None:
                    if not isinstance(act, Actor):
                        raise ValueError(
                            f"Neuron actor {key} is {act.__type__} but should be a vtkplotter Mesh. Not: {act}"
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
            neuron["soma"].c(colors["soma"][n])
            if neuron["dendrites"] is not None:
                neuron["dendrites"].c(colors["dendrites"][n])

        # Return
        return return_list_smart(_neurons_actors), None

    def get_tractography(
        self,
        tractography,
        color=None,
        color_by="manual",
        others_alpha=1,
        verbose=True,
        VIP_regions=[],
        VIP_color=None,
        others_color="white",
        include_all_inj_regions=False,
        extract_region_from_inj_coords=False,
        display_injection_volume=True,
    ):
        """
        Renders tractography data and adds it to the scene. A subset of tractography data can receive special treatment using the  with VIP regions argument:
        if the injection site for the tractography data is in a VIP regions, this is colored differently.

        :param tractography: list of dictionaries with tractography data
        :param color: color of rendered tractography data

        :param color_by: str, specifies which criteria to use to color the tractography (Default value = "manual")
        :param others_alpha: float (Default value = 1)
        :param verbose: bool (Default value = True)
        :param VIP_regions: list of brain regions with VIP treatement (Default value = [])
        :param VIP_color: str, color to use for VIP data (Default value = None)
        :param others_color: str, color for not VIP data (Default value = "white")
        :param include_all_inj_regions: bool (Default value = False)
        :param extract_region_from_inj_coords: bool (Default value = False)
        :param display_injection_volume: float, if True a spehere is added to display the injection coordinates and volume (Default value = True)
        """

        # check argument
        if not isinstance(tractography, list):
            if isinstance(tractography, dict):
                tractography = [tractography]
            else:
                raise ValueError(
                    "the 'tractography' variable passed must be a list of dictionaries"
                )
        else:
            if not isinstance(tractography[0], dict):
                raise ValueError(
                    "the 'tractography' variable passed must be a list of dictionaries"
                )

        if not isinstance(VIP_regions, list):
            raise ValueError("VIP_regions should be a list of acronyms")

        COLORS = parse_tractography_colors(
            tractography,
            color=color,
            color_by=color_by,
            VIP_regions=VIP_regions,
            VIP_color=VIP_color,
            others_color=others_color,
        )
        COLORS = [
            c
            if c is not None
            else self.get_region_color_from_acronym(t["structure-abbrev"])
            for c, t in zip(COLORS, tractography)
        ]

        # add actors to represent tractography data
        actors, structures_acronyms = [], []
        if brainrender.VERBOSE and verbose:
            print("Structures found to be projecting to target: ")

        # Loop over injection experiments
        for i, (t, color) in enumerate(zip(tractography, COLORS)):
            # Use allen metadata
            if include_all_inj_regions:
                inj_structures = [
                    x["abbreviation"] for x in t["injection-structures"]
                ]
            else:
                inj_structures = [
                    self.get_structure_parent(t["structure-abbrev"])["acronym"]
                ]

            if (
                brainrender.VERBOSE
                and verbose
                and not is_any_item_in_list(
                    inj_structures, structures_acronyms
                )
            ):
                print("     -- ({})".format(t["structure-abbrev"]))
                structures_acronyms.append(t["structure-abbrev"])

            # get tractography points and represent as list
            if color_by == "target_region" and not is_any_item_in_list(
                inj_structures, VIP_regions
            ):
                alpha = others_alpha
            else:
                alpha = brainrender.TRACTO_ALPHA

            if alpha == 0:
                continue  # skip transparent ones

            # check if we need to manually check injection coords
            if extract_region_from_inj_coords:
                try:
                    region = self.get_region_name_from_coords(
                        t["injection-coordinates"]
                    )
                    if region is None:
                        continue
                    inj_structures = [
                        self.get_structure_parent(region["acronym"])["acronym"]
                    ]
                except:
                    raise ValueError(
                        self.get_region_name_from_coords(
                            t["injection-coordinates"]
                        )
                    )
                if inj_structures is None:
                    continue
                elif isinstance(extract_region_from_inj_coords, list):
                    # check if injection coord are in one of the brain regions in list, otherwise skip
                    if not is_any_item_in_list(
                        inj_structures, extract_region_from_inj_coords
                    ):
                        continue

            # represent injection site as sphere
            if display_injection_volume:
                actors.append(
                    shapes.Sphere(
                        pos=t["injection-coordinates"],
                        c=color,
                        r=brainrender.INJECTION_VOLUME_SIZE
                        * t["injection-volume"],
                        alpha=brainrender.TRACTO_ALPHA,
                    )
                )

            points = [p["coord"] for p in t["path"]]
            actors.append(
                shapes.Tube(
                    points,
                    r=brainrender.TRACTO_RADIUS,
                    c=color,
                    alpha=alpha,
                    res=brainrender.TRACTO_RES,
                )
            )

        return actors

    def get_streamlines(
        self, sl_file, *args, colorby=None, color_each=False, **kwargs
    ):
        """
        Render streamline data downloaded from https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html

        :param sl_file: path to JSON file with streamliens data [or list of files]
        :param colorby: str,  criteria for how to color the streamline data (Default value = None)
        :param color_each: bool, if True, the streamlines for each injection is colored differently (Default value = False)
        :param *args:
        :param **kwargs:

        """
        color = None
        if not color_each:
            if colorby is not None:
                try:
                    color = self.structure_tree.get_structures_by_acronym(
                        [colorby]
                    )[0]["rgb_triplet"]
                    if "color" in kwargs.keys():
                        del kwargs["color"]
                except:
                    raise ValueError(
                        "Could not extract color for region: {}".format(
                            colorby
                        )
                    )
        else:
            if colorby is not None:
                color = kwargs.pop("color", None)
                try:
                    get_n_shades_of(color, 1)
                except:
                    raise ValueError(
                        "Invalide color argument: {}".format(color)
                    )

        if not isinstance(sl_file, (list, tuple)):
            sl_file = [sl_file]

        actors = []
        if isinstance(
            sl_file[0], (str, pd.DataFrame)
        ):  # we have a list of files to add
            for slf in tqdm(sl_file):
                if not color_each:
                    if color is not None:
                        if isinstance(slf, str):
                            streamlines = parse_streamline(
                                filepath=slf, *args, color=color, **kwargs
                            )
                        else:
                            streamlines = parse_streamline(
                                data=slf, *args, color=color, **kwargs
                            )
                    else:
                        if isinstance(slf, str):
                            streamlines = parse_streamline(
                                filepath=slf, *args, **kwargs
                            )
                        else:
                            streamlines = parse_streamline(
                                data=slf, *args, **kwargs
                            )
                else:
                    if color is not None:
                        col = get_n_shades_of(color, 1)[0]
                    else:
                        col = get_random_colors(n_colors=1)
                    if isinstance(slf, str):
                        streamlines = parse_streamline(
                            filepath=slf, color=col, *args, **kwargs
                        )
                    else:
                        streamlines = parse_streamline(
                            data=slf, color=col, *args, **kwargs
                        )
                actors.extend(streamlines)
        else:
            raise ValueError(
                "unrecognized argument sl_file: {}".format(sl_file)
            )

        return actors

    def get_injection_sites(self, experiments, color=None):
        """
        Creates Spherse at the location of injections with a volume proportional to the injected volume

        :param experiments: list of dictionaries with tractography data
        :param color:  (Default value = None)

        """
        # check arguments
        if not isinstance(experiments, list):
            raise ValueError("experiments must be a list")
        if not isinstance(experiments[0], dict):
            raise ValueError("experiments should be a list of dictionaries")

        # c= cgeck color
        if color is None:
            color = INJECTION_DEFAULT_COLOR

        injection_sites = []
        for exp in experiments:
            injection_sites.append(
                shapes.Sphere(
                    pos=(
                        exp["injection_x"],
                        exp["injection_y"],
                        exp["injection_z"],
                    ),
                    r=INJECTION_VOLUME_SIZE * exp["injection_volume"] * 3,
                    c=color,
                )
            )

        return injection_sites

    # ----------------------------------- Utils ---------------------------------- #
    def get_projection_tracts_to_target(self, p0=None, **kwargs):
        """
        Gets tractography data for all experiments whose projections reach the brain region or location of iterest.
        
        :param p0: list of 3 floats with XYZ coordinates of point to be used as seed (Default value = None)
        :param **kwargs: 
        """

        # check args
        if p0 is None:
            raise ValueError("Please pass coordinates")
        elif isinstance(p0, np.ndarray):
            p0 = list(p0)
        elif not isinstance(p0, (list, tuple)):
            raise ValueError("Invalid argument passed (p0): {}".format(p0))

        p0 = [np.int(p) for p in p0]
        tract = self.mca.experiment_spatial_search(seed_point=p0, **kwargs)

        if isinstance(tract, str):
            raise ValueError(
                "Something went wrong with query, query error message:\n{}".format(
                    tract
                )
            )
        else:
            return tract

    def download_streamlines_for_region(self, region, *args, **kwargs):
        """
            Using the Allen Mouse Connectivity data and corresponding API, this function finds expeirments whose injections
            were targeted to the region of interest and downloads the corresponding streamlines data. By default, experiements
            are selected for only WT mice and onl when the region was the primary injection target. Look at "ABA.experiments_source_search"
            to see how to change this behaviour.

            :param region: str with region to use for research
            :param *args: arguments for ABA.experiments_source_search
            :param **kwargs: arguments for ABA.experiments_source_search

        """
        # Get experiments whose injections were targeted to the region
        region_experiments = experiments_source_search(
            self.mca, region, *args, **kwargs
        )
        try:
            return download_streamlines(
                region_experiments.id.values,
                streamlines_folder=self.streamlines_cache,
            )
        except:
            print(f"Could not download streamlines for region {region}")
            return [], []  # <- there were no experiments in the target region

    def download_streamlines_to_region(
        self, p0, *args, mouse_line="wt", **kwargs
    ):
        """
            Using the Allen Mouse Connectivity data and corresponding API, this function finds injection experiments
            which resulted in fluorescence being found in the target point, then downloads the streamlines data.

            :param p0: list of floats with XYZ coordinates
            :param mouse_line: str with name of the mouse line to use(Default value = "wt")
            :param *args: 
            :param **kwargs: 

        """
        experiments = pd.DataFrame(self.get_projection_tracts_to_target(p0=p0))
        if mouse_line == "wt":
            experiments = experiments.loc[experiments["transgenic-line"] == ""]
        else:
            if not isinstance(mouse_line, list):
                experiments = experiments.loc[
                    experiments["transgenic-line"] == mouse_line
                ]
            else:
                raise NotImplementedError(
                    "ops, you've found a bug!. For now you can only pass one mouse line at the time, sorry."
                )
        return download_streamlines(
            experiments.id.values, streamlines_folder=self.streamlines_cache
        )


# ---------------------------------------------------------------------------- #
#                          RESOLUTION SPECIFIC CLASSES                         #
# ---------------------------------------------------------------------------- #

"""
    These classes bring together ABA (above) with the mouse atlases supported
    by the brainglobe API
"""


class ABA25Um(ABA, AllenBrain25Um):
    atlas_name = "allenbrain25um"

    resolution = 25

    _root_bounds = [[-17, 13193], [134, 7564], [486, 10891]]

    _root_midpoint = [
        np.mean([-17, 13193]),
        np.mean([134, 7564]),
        np.mean([486, 10891]),
    ]

    def __init__(self, base_dir=None, **kwargs):
        ABA.__init__(self, base_dir=base_dir, **kwargs)
        AllenBrain25Um.__init__(self)

        self.meshes_folder = self.root_dir / "meshes"
