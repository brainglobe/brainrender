"""Utilities for caching and loading Allen Brain Atlas gene expression data."""

import io
import os
import sys
import zipfile
from typing import Literal
from pathlib import Path

import numpy as np
import numpy.typing as npt

from brainrender._io import check_file_exists, request
from brainrender._utils import get_subdirs, listdir

# ----------------------------------- Cache ---------------------------------- #


def check_gene_cached(
    cache_folder: str | Path,
    gene_id: str,
    exp_id: str | int,
) -> str | Literal[False]:
    """
    Check whether a gene experiment is already cached.

    A gene is cached in a subfolder of ``cache_folder`` named
    ``{gene_id}-{exp_id}``.

    Parameters
    ----------
    cache_folder
        Path to the general cache folder.
    gene_id
        Gene name.
    exp_id
        Experiment ID.

    Returns
    -------
    str or False
        Path to the cached folder if found, False if not cached.

    Raises
    ------
    ValueError
        If more than one matching folder is found.
    """
    cache = [
        sub
        for sub in get_subdirs(cache_folder)
        if f"{gene_id}-{exp_id}" == os.path.basename(sub)
    ]
    if not cache:
        return False
    elif len(cache) > 1:
        raise ValueError("Found too many folders")
    else:
        return cache[0]


def download_and_cache(url: str, cachedir: str | Path) -> None:
    """
    Download and unzip a gene's ISH experiment data to a cache directory.

    Parameters
    ----------
    url
        URL to download the data from.
    cachedir
        Path to the folder where data will be saved.
    """
    # Get data
    req = request(url)

    # Create cache dir
    if not os.path.isdir(cachedir):
        os.mkdir(cachedir)

    # Unzip to cache dir
    z = zipfile.ZipFile(io.BytesIO(req.content))
    z.extractall(cachedir)


def load_cached_gene(
    cache: str | Path,
    metric: str,
    grid_size: tuple[int, int, int],
) -> npt.NDArray | None:
    """
    Load a gene's data from cache.

    Parameters
    ----------
    cache
        Path to the gene's cache folder.
    metric
        Metric name used to filter files (e.g. ``"energy"``).
    grid_size
        Shape to use when reshaping the raw data array.

    Returns
    -------
    numpy.ndarray or None
        Array of gene expression values, or None if no file is found.

    Raises
    ------
    NotImplementedError
        If more than one matching file is found.
    """
    files = [
        f for f in listdir(cache) if metric in f and not f.endswith(".mhd")
    ]
    if not files:
        return None
    if len(files) > 1:
        raise NotImplementedError("Deal with more than one file found")
    else:
        return read_raw(files[0], grid_size)


# --------------------------------- Open .raw -------------------------------- #
@check_file_exists
def read_raw(
    filepath: str | Path,
    grid_size: tuple[int, int, int],
) -> npt.NDArray:
    """
    Read a ``.raw`` gene expression file from the Allen Brain Atlas.

    See http://help.brain-map.org/display/mousebrain/API#API-Expression3DGridsz
    for the file format reference.

    Parameters
    ----------
    filepath
        Path to the ``.raw`` file.
    grid_size
        Shape to use when reshaping the data array.

    Returns
    -------
    numpy.ndarray
    """
    filepath = str(filepath)

    # Read bytes
    with open(filepath, "rb") as test:
        content = test.read()

    # Create np array and return
    data = np.frombuffer(content, dtype="float32").reshape(grid_size)

    if sys.platform == "darwin":
        data = data.T  # TODO figure out why this is necessary on Mac OS?

    return data
