import pandas as pd
import numpy as np
import requests as http_requests
from loguru import logger
from myterial import orange
from rich import print
from rich.progress import track

try:
    from allensdk.api.queries.mouse_connectivity_api import (
        MouseConnectivityApi,
    )

    mca = MouseConnectivityApi()
    allen_sdk_installed = True
except ModuleNotFoundError:  # pragma: no cover
    allen_sdk_installed = False  # pragma: no cover

try:
    import cloudvolume

    cloudvolume_installed = True
except ModuleNotFoundError:  # pragma: no cover
    cloudvolume_installed = False  # pragma: no cover


from brainrender import base_dir
from brainrender._utils import listify

streamlines_folder = base_dir / "streamlines"
streamlines_folder.mkdir(exist_ok=True)

ALLEN_MESOSCALE_URL = "precomputed://gs://allen_neuroglancer_ccf/allen_mesoscale"
ALLEN_API_URL = "https://api.brain-map.org/api/v2/data/query.json"
VOXEL_SIZE_NM = 1000  # skeleton vertices are in nanometers
DV_EXTENT_UM = 8000.0  # 320 voxels * 25um = full DV extent of Allen CCF


def experiments_source_search(SOI):
    """
    Returns data about experiments whose injection was in the SOI, structure of interest
    :param SOI: str, structure of interest. Acronym of structure to use as seed for the search
    """
    transgenic_id = 0  # id = 0 means use only wild type
    primary_structure_only = True

    if not allen_sdk_installed:
        print(
            f"[{orange}]Streamlines cannot be downloaded because the AllenSDK package is not installed. "
            "Please install `allensdk` with `pip install allensdk`"
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


def _get_injection_site_um(eid):
    """
    Fetches the injection site coordinates for an experiment from the Allen
    Brain Atlas API. Coordinates are returned in the same um space as the
    streamline vertices (x, y_flipped, z).

    Uses the ProjectionStructureUnionize endpoint which provides max_voxel
    coordinates in Allen CCF um space for the injection site voxel.

    :param eid: int, experiment ID
    :return: dict with x, y, z keys or None if not found
    """
    try:
        url = (
            f"{ALLEN_API_URL}?q=model::ProjectionStructureUnionize,"
            f"rma::criteria,section_data_set[id$eq{eid}],"
            f"rma::criteria,[is_injection$eqtrue],"
            f"rma::options[num_rows$eq1][order$eq'projection_volume desc']"
        )
        response = http_requests.get(url, timeout=10)
        data = response.json()
        if data["success"] and data["num_rows"] > 0:
            voxel = data["msg"][0]
            x = float(voxel["max_voxel_x"])
            y = float(DV_EXTENT_UM - voxel["max_voxel_y"])  # flip DV axis
            z = float(voxel["max_voxel_z"])
            return {"x": x, "y": y, "z": z}
    except Exception as e:
        logger.warning(f"Could not fetch injection site for experiment {eid}: {e}")
    return None


def _skeleton_to_dataframe(skeleton, eid):
    """
    Converts a cloudvolume Skeleton object to the pd.DataFrame format
    expected by brainrender's Streamlines actor.

    Vertices are in nanometers and in Allen CCF PIR space. We:
    1. Convert nm -> um (divide by VOXEL_SIZE_NM)
    2. Flip the y (DV) axis to match brainrender's ASR orientation

    The injection site is fetched from the Allen API using the experiment ID.
    If unavailable, falls back to the centroid of all skeleton vertices.

    :param skeleton: cloudvolume Skeleton object
    :param eid: int, experiment ID used to fetch real injection coordinates
    :return: pd.DataFrame with 'lines' and 'injection_sites' columns
    """
    components = skeleton.components()

    lines = []
    for component in components:
        verts_um = component.vertices / VOXEL_SIZE_NM
        points = [
            {
                "x": float(v[0]),
                "y": float(DV_EXTENT_UM - v[1]),  # flip DV axis
                "z": float(v[2]),
            }
            for v in verts_um
        ]
        lines.append(points)

    # get real injection site from Allen API, fall back to centroid
    injection_site = _get_injection_site_um(eid)
    if injection_site is None:
        logger.warning(
            f"Falling back to centroid for injection site of experiment {eid}"
        )
        all_verts_um = skeleton.vertices / VOXEL_SIZE_NM
        centroid = all_verts_um.mean(axis=0)
        injection_site = {
            "x": float(centroid[0]),
            "y": float(DV_EXTENT_UM - centroid[1]),
            "z": float(centroid[2]),
        }

    return pd.DataFrame({
        "lines": [lines],
        "injection_sites": [[injection_site]],
    })


def get_streamlines_data(eids, force_download=False):
    """
    Given a list of experiment IDs, downloads streamline data from the
    Allen mesoscale connectivity dataset hosted on Google Cloud Storage
    via cloud-volume, and saves them as JSON files.

    :param eids: list of integers with experiment IDs
    :param force_download: bool, if True re-download even if cached
    """
    if not cloudvolume_installed:
        print(
            f"[{orange}]Streamlines cannot be downloaded because the cloud-volume package is not installed. "
            "Please install it with `pip install cloud-volume`"
        )
        return []

    cv = cloudvolume.CloudVolume(
        ALLEN_MESOSCALE_URL,
        use_https=True,
        progress=False,
    )

    data = []
    for eid in track(eids, total=len(eids), description="downloading"):
        jsonpath = streamlines_folder / f"{eid}.json"

        if not jsonpath.exists() or force_download:
            try:
                skeleton = cv.skeleton.get(int(eid))
            except Exception as e:
                logger.warning(
                    f"Could not fetch streamlines for experiment {eid}: {e}"
                )
                continue

            df = _skeleton_to_dataframe(skeleton, int(eid))
            df.to_json(str(jsonpath))
            data.append(df)
        else:
            data.append(pd.read_json(str(jsonpath)))

    return data


def get_streamlines_for_region(region, force_download=False):
    """
    Using the Allen Mouse Connectivity data and corresponding API, this function finds experiments
    whose injections were targeted to the region of interest and downloads the corresponding
    streamlines data from the Allen mesoscale connectivity dataset on Google Cloud Storage.
    By default, experiments are selected for only WT mice and only when the region was
    the primary injection target.

    :param region: str with region to use for search
    :param force_download: bool, if True re-download even if cached
    """
    logger.debug(f"Getting streamlines data for region: {region}")
    region_experiments = experiments_source_search(region)
    if region_experiments is None or region_experiments.empty:
        logger.debug("No experiments found from allen data")
        return None

    return get_streamlines_data(
        region_experiments.id.values, force_download=force_download
    )
