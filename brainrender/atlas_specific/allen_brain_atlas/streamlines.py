"""Streamline download and conversion utilities for the Allen Mouse Brain Atlas."""

from typing import Any

import pandas as pd
import requests
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

from brainglobe_atlasapi import BrainGlobeAtlas

from brainrender import base_dir
from brainrender._utils import listify

streamlines_folder = base_dir / "streamlines"
streamlines_folder.mkdir(exist_ok=True)

ALLEN_MESOSCALE_URL = (
    "precomputed://gs://allen_neuroglancer_ccf/allen_mesoscale"
)
ALLEN_API_URL = "https://api.brain-map.org/api/v2/data/query.json"
VOXEL_SIZE_NM = 1000  # skeleton vertices are in nanometers

_ml_extent_um_cache: float | None = None


def _get_ml_extent_um() -> float:
    """
    Derive the full medial-lateral extent of the Allen CCF atlas in microns
    dynamically from the brainglobe atlas API. The computed extent is cached
    for subsequent calls and used to flip the Z (ML) axis when converting
    from Allen CCF space to brainrender's coordinate system.

    Returns
    -------
    float
        Full medial-lateral extent of the atlas in microns.
    """
    global _ml_extent_um_cache
    if _ml_extent_um_cache is None:
        atlas = BrainGlobeAtlas("allen_mouse_25um", check_latest=False)
        _ml_extent_um_cache = float(atlas.shape[2] * atlas.resolution[2])
    return _ml_extent_um_cache


def experiments_source_search(SOI: str) -> pd.DataFrame | None:
    """
    Return data about experiments whose injection was in the structure of interest.

    Parameters
    ----------
    SOI
        Acronym of the structure of interest to use as the search seed.

    Returns
    -------
    pd.DataFrame or None
        DataFrame of matching experiments, or None if AllenSDK is not installed.
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


def _get_injection_site_um(
    eid: int,
    ml_extent_um: float,
) -> dict[str, float] | None:
    """
    Fetch injection site coordinates for an experiment from the Allen Brain Atlas API.
    Coordinates are returned in Allen CCF µm space with the Z (ML) axis
    flipped to match brainrender's hemisphere convention.

    Parameters
    ----------
    eid
        Experiment ID.
    ml_extent_um
        Full ML extent of the atlas in µm, used for the left-right flip.

    Returns
    -------
    dict or None
        Dict with ``x``, ``y``, ``z`` keys in µm, or None if not found.
    """
    try:
        url = (
            f"{ALLEN_API_URL}?q=model::ProjectionStructureUnionize,"
            f"rma::criteria,section_data_set[id$eq{eid}],"
            f"rma::criteria,[is_injection$eqtrue],"
            f"rma::options[num_rows$eq1][order$eq'projection_volume desc']"
        )
        response = requests.get(url, timeout=10)
        data = response.json()
        if data["success"] and data["num_rows"] > 0:
            voxel = data["msg"][0]
            return {
                "x": float(voxel["max_voxel_x"]),
                "y": float(voxel["max_voxel_y"]),
                "z": float(ml_extent_um - voxel["max_voxel_z"]),
            }
    except Exception as e:
        logger.warning(
            f"Could not fetch injection site for experiment {eid}: {e}"
        )
    return None


def _skeleton_to_dataframe(
    skeleton: Any,
    eid: int,
    ml_extent_um: float,
) -> pd.DataFrame:
    """
    Convert a cloudvolume Skeleton object to a DataFrame for the Streamlines actor.

    Vertices are in nanometers in Allen CCF space. We:
    1. Convert nm -> um (divide by VOXEL_SIZE_NM)
    2. Flip Z (ML) axis to match brainrender's hemisphere convention

    X (AP) and Y (DV) are passed through as-is because brainrender's
    brain mesh uses the same orientation as the Allen CCF for those axes.

    Parameters
    ----------
    skeleton
        cloudvolume Skeleton object.
    eid
        Experiment ID, used to fetch the real injection site coordinates.
    ml_extent_um
        Full ML extent of the atlas in µm, used for the left-right flip.
 
    Returns
    -------
    pd.DataFrame
        DataFrame with ``lines`` and ``injection_sites`` columns.
    """
    components = skeleton.components()

    lines = []
    for component in components:
        verts_um = component.vertices / VOXEL_SIZE_NM
        points = [
            {
                "x": float(v[0]),
                "y": float(v[1]),
                "z": float(ml_extent_um - v[2]),
            }
            for v in verts_um
        ]
        lines.append(points)

    injection_site = _get_injection_site_um(eid, ml_extent_um)
    if injection_site is None:
        logger.warning(
            f"Falling back to centroid for injection site of experiment {eid}"
        )
        all_verts_um = skeleton.vertices / VOXEL_SIZE_NM
        centroid = all_verts_um.mean(axis=0)
        injection_site = {
            "x": float(centroid[0]),
            "y": float(centroid[1]),
            "z": float(ml_extent_um - centroid[2]),
        }

    return pd.DataFrame(
        {"lines": [lines], "injection_sites": [[injection_site]]}
    )


def get_streamlines_data(
    eids: list[int],
    force_download: bool = False,
) -> list[pd.DataFrame]:
    """
    Given a list of experiment IDs, download streamline data from the
    Allen mesoscale connectivity dataset hosted on Google Cloud Storage
    via cloud-volume, and save them as JSON files.

    Parameters
    ----------
    eids
        Experiment IDs to download.
    force_download
        If True, re-download even if a cached file exists. Default False.

    Returns
    -------
    list of pd.DataFrame
    """
    if not cloudvolume_installed:
        print(
            f"[{orange}]Streamlines cannot be downloaded because the cloud-volume package is not installed. "
            "Please install it with `pip install cloud-volume`"
        )
        return []

    ml_extent_um = _get_ml_extent_um()

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

            df = _skeleton_to_dataframe(skeleton, int(eid), ml_extent_um)
            df.to_json(str(jsonpath))
            data.append(df)
        else:
            data.append(pd.read_json(str(jsonpath)))

    return data


def get_streamlines_for_region(
    region: str,
    force_download: bool = False,
) -> list[pd.DataFrame] | None:
    """
    Using the Allen Mouse Connectivity data and corresponding API, this function finds experiments
    whose injections were targeted to the region of interest and downloads the corresponding
    streamlines data from the Allen mesoscale connectivity dataset on Google Cloud Storage.
    By default, experiments are selected for only WT mice and only when the region was
    the primary injection target.

    Parameters
    ----------
    region
        Acronym of the brain region to search for.
    force_download
        If True, re-download even if cached. Default False.

    Returns
    -------
    list of pd.DataFrame or None
        Streamlines data, or None if no experiments are found.
    """
    logger.debug(f"Getting streamlines data for region: {region}")
    region_experiments = experiments_source_search(region)
    if region_experiments is None or region_experiments.empty:
        logger.debug("No experiments found from allen data")
        return None

    return get_streamlines_data(
        region_experiments.id.values, force_download=force_download
    )
