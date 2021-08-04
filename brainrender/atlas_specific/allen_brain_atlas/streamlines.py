import pandas as pd
from rich.progress import track
from rich import print
from loguru import logger
from myterial import orange

try:
    from allensdk.api.queries.mouse_connectivity_api import (
        MouseConnectivityApi,
    )

    mca = MouseConnectivityApi()
    allen_sdk_installed = True
except ModuleNotFoundError:  # pragma: no cover
    allen_sdk_installed = False  # pragma: no cover


from brainrender._utils import listify
from brainrender._io import request
from brainrender import base_dir

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

    if not allen_sdk_installed:
        print(
            f"[{orange}]Allen skd package is not installed, cannot download streamlines data."
            "Please install `allensdk` with `pip install allensdk` (note: this requires python < 3.8)"
        )
        return None

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
    logger.debug(f"Getting streamlines data for region: {region}")
    # Get experiments whose injections were targeted to the region
    region_experiments = experiments_source_search(region)
    if region_experiments is None or region_experiments.empty:
        logger.debug("No experiments found from allen data")
        return None

    return get_streamlines_data(
        region_experiments.id.values, force_download=force_download
    )
