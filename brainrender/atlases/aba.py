import os
import numpy as np
import pandas as pd
from rich.progress import track
from vedo import shapes, merge, Mesh
from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
from allensdk.api.queries.ontologies_api import OntologiesApi
from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
from allensdk.api.queries.tree_search_api import TreeSearchApi
from allensdk.core.reference_space_cache import ReferenceSpaceCache
from morphapi.morphology.morphology import Neuron

import brainrender
from brainrender.morphology.utils import get_neuron_actors_with_morphapi
from brainrender.ABA.aba_utils import (
    parse_streamline,
    download_streamlines,
    experiments_source_search,
    parse_neurons_colors,
    parse_tractography_colors,
)
from brainrender.Utils.data_manipulation import (
    return_list_smart,
    is_any_item_in_list,
)


class ABA:
    """
        This class augments the functionality of
        BrainGlobeAtlas with methods specific to the Allen
        Mouse Brain atlas and necessary to populate scenes in 
        brainrender. These include stuff like fetching streamlines
        and neuronal morphology data. 
    """

    atlas_name = "ABA"
    resolution = 25

    excluded_regions = ["fiber tracts"]

    # Used for streamlines
    base_url = "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_NNN.json.gz"

    def __init__(self):
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
            resolution=int(self.resolution[0]),
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
        soma_radius=None,
        use_cache=True,
    ):
        """
        Gets rendered morphological data of neurons reconstructions downloaded from the
        Mouse Light project at Janelia (or other sources). 
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
        display_injection_volume=True,
    ):
        """
        Renders tractography data and adds it to the scene. A subset of tractography data can receive special treatment using the  with VIP regions argument:
        if the injection site for the tractography data is in a VIP regions, this is colored differently.

        :param tractography: list of dictionaries with tractography data
        :param color: color of rendered tractography data

        :param color_by: str, specifies which criteria to use to color the tractography (Default value = "manual")
                        options:
                            -  manual, define color of each tract
                            - target_region, color by the injected region

        :param others_alpha: float (Default value = 1)
        :param verbose: bool (Default value = True)
        :param VIP_regions: list of brain regions with VIP treatement (Default value = [])
        :param VIP_color: str, color to use for VIP data (Default value = None)
        :param others_color: str, color for not VIP data (Default value = "white")
        :param include_all_inj_regions: bool (Default value = False)
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
            include_all_inj_regions,
            color=color,
            color_by=color_by,
            VIP_regions=VIP_regions,
            VIP_color=VIP_color,
            others_color=others_color,
        )
        COLORS = [
            c
            if c is not None
            else self._get_from_structure(t["structure-abbrev"], "rgb_triplet")
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
                    self.get_structure_ancestors(t["structure-abbrev"])[-1]
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
                actors[-1].name = (
                    str(t["injection-coordinates"]) + "_injection"
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
            actors[-1].name = str(t["injection-coordinates"]) + "_tractography"

        return actors

    def get_streamlines(self, sl_file, color=None, *args, **kwargs):
        """
        Render streamline data downloaded from https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html

        :param sl_file: path to JSON file with streamliens data [or list of files]
        :param color: either a single color or a list of colors to color each streamline individually
        :param *args:
        :param **kwargs:

        """
        if not isinstance(sl_file, (list, tuple)):
            sl_file = [sl_file]

        # get a list of colors of length len(sl_file)
        if color is not None:
            if isinstance(color, (list, tuple)):
                if isinstance(color[0], (float, int)):  # it's an rgb color
                    color = [color for i in sl_file]
                elif len(color) != len(sl_file):
                    raise ValueError(
                        "Wrong number of colors, should be one per streamline or 1"
                    )
            else:
                color = [color for i in sl_file]
        else:
            color = ["salmon" for i in sl_file]

        actors = []
        if isinstance(
            sl_file[0], (str, pd.DataFrame)
        ):  # we have a list of files to add
            for slf, col in track(
                zip(sl_file, color),
                total=len(sl_file),
                description="parsing streamlines",
            ):
                if isinstance(slf, str):
                    streamlines = parse_streamline(
                        color=col, filepath=slf, *args, **kwargs
                    )
                else:
                    streamlines = parse_streamline(
                        color=col, data=slf, *args, **kwargs
                    )
                actors.extend(streamlines)
        else:
            raise ValueError(
                "unrecognized argument sl_file: {}".format(sl_file)
            )

        return actors

    # ----------------------------------- Utils ---------------------------------- #
    def get_projection_tracts_to_target(self, p0=None, **kwargs):
        """
        Gets tractography data for all experiments whose projections reach the brain region or location of iterest.
        
        :param p0: list of 3 floats with AP-DV-ML coordinates of point to be used as seed (Default value = None)
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

            :param p0: list of floats with AP-DV-ML coordinates
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
