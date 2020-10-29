import pandas as pd
from vedo.shapes import Tube
from vedo import merge
from rich.progress import track

try:
    from allensdk.api.queries.mouse_connectivity_api import (
        MouseConnectivityApi,
    )

    mca = MouseConnectivityApi()
    allen_sdk_installed = True
except ModuleNotFoundError:
    allen_sdk_installed = False


from brainrender import base_dir
from .._utils import listify
from .._io import request
from ..actor import Actor

streamlines_folder = base_dir / "streamlines"
streamlines_folder.mkdir(exist_ok=True)


def experiments_source_search(SOI):
    """
        Returns data about experiments whose injection was in the SOI, structure of interest
        :param SOI: str, structure of interest. Acronym of structure to use as seed for teh search
        :param source:  (Default value = True)
    """

    transgenic_id = 0  # id = 0 means use only wild type
    primary_structure_only = True

    return pd.DataFrame(
        mca.experiment_source_search(
            injection_structures=listify(SOI),
            target_domain=None,
            transgenic_lines=transgenic_id,
            primary_structure_only=primary_structure_only,
        )
    )


def get_streamlines_data(eids, force_download=False):
    """
        Given a list of expeirmental IDs, it downloads the streamline data 
        from the https://neuroinformatics.nl cache and saves them as
        json files. 

        :param eids: list of integers with experiments IDs
    """
    data = []
    for eid in track(eids, total=len(eids), description="downloading"):
        url = "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_{}.json.gz".format(
            eid
        )

        jsonpath = streamlines_folder / f"{eid}.json"

        if not jsonpath.exists() or force_download:
            response = request(url)

            # Write the response content as a temporary compressed file
            temp_path = streamlines_folder / "temp.gz"
            with open(str(temp_path), "wb") as temp:
                temp.write(response.content)

            # Open in pandas and delete temp
            url_data = pd.read_json(
                str(temp_path), lines=True, compression="gzip"
            )
            temp_path.unlink()

            # save json
            url_data.to_json(str(jsonpath))

            # append to lists and return
            data.append(url_data)
        else:
            data.append(pd.read_json(str(jsonpath)))
    return data


def get_streamlines_for_region(region, force_download=False):
    """
        Using the Allen Mouse Connectivity data and corresponding API, this function finds expeirments whose injections
        were targeted to the region of interest and downloads the corresponding streamlines data. By default, experiements
        are selected for only WT mice and onl when the region was the primary injection target.

        :param region: str with region to use for research

    """
    # Get experiments whose injections were targeted to the region
    region_experiments = experiments_source_search(region)

    return get_streamlines_data(
        region_experiments.id.values, force_download=force_download
    )


def make_streamlines(*streamlines, color="salmon", alpha=1, radius=10):
    """
        Creates instances of Streamlines from data.
        :param streamlines: pd.dataframes with streamlines data
        :param radius: float. Radius of the Tube mesh used to render streamlines
        :param color: str, name of the color to be used
        :param alpha: float, transparancy
    """
    return [
        Streamlines(s, color=color, alpha=alpha, radius=radius)
        for s in streamlines
    ]


class Streamlines(Actor):
    """ 
        Streamliens actor class.
        Creates an actor from streamlines data (from a json file parsed with: get_streamlines_data)
    """

    def __init__(self, data, radius=10, color="salmon", alpha=1, name=None):
        """
            Turns streamlines data to a mesh.
            :param data: pd.DataFrame with streamlines points data
            :param radius: float. Radius of the Tube mesh used to render streamlines
            :param color: str, name of the color to be used
            :param alpha: float, transparancy
            :param name: str, name of the actor.
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data should be a dataframe")

        self.radius = radius
        mesh = self._make_mesh(data).c(color).alpha(alpha)

        name = name or "Streamlines"
        Actor.__init__(self, mesh, name=name, br_class="Streamliness")

    def _make_mesh(self, data):
        lines = []
        if len(data["lines"]) == 1:
            try:
                lines_data = data["lines"][0]
            except KeyError:
                lines_data = data["lines"]["0"]
        else:
            lines_data = data["lines"]
        for line in lines_data:
            points = [[l["x"], l["y"], l["z"]] for l in line]
            lines.append(Tube(points, r=self.radius, res=8,))

        return merge(*lines)
