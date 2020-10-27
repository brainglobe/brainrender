import pandas as pd
from rich.progress import track


try:
    from allensdk.api.queries.mouse_connectivity_api import (
        MouseConnectivityApi,
    )

    allen_sdk_installed = True
except ModuleNotFoundError:
    allen_sdk_installed = False


from brainrender.ABA.aba_utils import (
    parse_streamline,
    download_streamlines,
    experiments_source_search,
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

    excluded_regions = ["fiber tracts"]

    # Used for streamlines
    base_url = "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_NNN.json.gz"

    def __init__(self):
        # mouse connectivity API [used for tractography]
        if allen_sdk_installed:
            self.mca = MouseConnectivityApi()
        else:
            self.mca = None

    # ------------------------- Scene population methods ------------------------- #

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
        if self.mca is None:
            raise ModuleNotFoundError(
                'You need allen sdk to use this functino: "pip install allensdk"'
            )

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
