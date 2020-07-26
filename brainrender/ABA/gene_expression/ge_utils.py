import os
import numpy as np
import zipfile
import io
import sys
from brainrender.Utils.data_io import get_subdirs, listdir
from brainrender.Utils.webqueries import request
from brainrender.Utils.decorators import check_file_exists

# ----------------------------------- Cache ---------------------------------- #


def check_gene_cached(cache_folder, gene_id, exp_id):
    """ 
        A gene is saved in a folder in cache_folder
        with gene_id-exp_id as name. If the folder doesn't
        exist the gene is not cached.

        :param cache_folder: str, path to general cache folder for all data
        :param gene_id: str name of gene
        :param exp_id: id of experiment 
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


def download_and_cache(url, cachedir):
    """
        Given a url to download a gene's ISH experiment data, 
        this function download and unzips the data

        :param url: str, utl to download data
        :param cachedir: str, path to folder where data will be downloaded
    """
    # Get data
    req = request(url)

    # Create cache dir
    if not os.path.isdir(cachedir):
        os.mkdir(cachedir)

    # Unzip to cache dir
    z = zipfile.ZipFile(io.BytesIO(req.content))
    z.extractall(cachedir)


def load_cached_gene(cache, metric, grid_size):
    """
        Loads a gene's data from cache
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
def read_raw(filepath, grid_size):
    """
        reads a .raw file with gene expression data 
        downloaded from the Allen atlas and returns 
        a numpy array with the correct grid_size.
        See as reference:
            http://help.brain-map.org/display/mousebrain/API#API-Expression3DGridsz

        :param filepath: str or Path object
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
