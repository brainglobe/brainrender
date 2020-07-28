from pathlib import Path
import json
import yaml
import gzip
import numpy as np
import scipy.io as sio
import pandas as pd
from brainio import brainio
from vedo import load
import brainrender
from brainrender.Utils.decorators import check_file_exists

# ------------------------------------ OS ------------------------------------ #


def listdir(fld):
    """
    List the files into a folder with the complete file path instead of the relative file path like os.listdir.

    :param fld: string, folder path

    """
    return [str(f) for f in Path(fld).glob("**/*") if f.is_file()]


def get_subdirs(folderpath):
    """
        Returns the subfolders in a given folder
    """
    return [str(f) for f in Path(folderpath).glob("**/*") if f.is_dir()]


# ------------------------------ Load/Save data ------------------------------ #
@check_file_exists
def load_cells_from_file(filepath, hdf_key="hdf"):
    csv_suffix = ".csv"
    supported_formats = brainrender.HDF_SUFFIXES + [csv_suffix]

    #  check that the filepath makes sense
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(filepath)

    # check that the file is of the supported types
    if filepath.suffix == csv_suffix:
        cells = pd.read_csv(filepath)

    elif filepath.suffix in supported_formats:
        # parse file and load cell locations
        try:
            # Try reading without hdf key
            cells = pd.read_hdf(filepath)

        except KeyError:
            # Try reading with hdf key
            if filepath.suffix in brainrender.HDF_SUFFIXES:
                if hdf_key is None:
                    hdf_key = brainrender.DEFAULT_HDF_KEY
                try:
                    cells = pd.read_hdf(filepath, key=hdf_key)
                except KeyError:
                    if hdf_key == brainrender.DEFAULT_HDF_KEY:
                        raise ValueError(
                            f"The default identifier: {brainrender.DEFAULT_HDF_KEY} "
                            f"cannot be found in the hdf file. Please supply "
                            f"a key using 'scene.add_cells_from_file(filepath, "
                            f"hdf_key='key'"
                        )
                    else:
                        raise ValueError(
                            f"The key: {hdf_key} cannot be found in the hdf "
                            f"file. Please check the correct identifer."
                        )

    elif filepath.suffix == ".pkl":
        cells = pd.read_pikle(filepath)

    else:
        raise NotImplementedError(
            f"File format: {filepath.suffix} is not currently supported. "
            f"Please use one of: {supported_formats + ['.pkl']}"
        )

    return cells, filepath.name


@check_file_exists
def load_npy_from_gz(filepath):
    f = gzip.GzipFile(filepath, "r")
    return np.load(f)


def save_npy_to_gz(filepath, data):
    f = gzip.GzipFile(filepath, "w")
    np.save(f, data)
    f.close()


def save_yaml(filepath, content, append=False, topcomment=None):
    """
    Saves content to a yaml file

    :param filepath: path to a file (must include .yaml)
    :param content: dictionary of stuff to save

    """
    if "yaml" not in filepath:
        raise ValueError("filepath is invalid")

    if not append:
        method = "w"
    else:
        method = "w+"

    with open(filepath, method) as yaml_file:
        if topcomment is not None:
            yaml_file.write(topcomment)
        yaml.dump(content, yaml_file, default_flow_style=False, indent=4)


@check_file_exists
def load_json(filepath):
    """
    Load a JSON file

    :param filepath: path to a file

    """
    with open(filepath) as f:
        data = json.load(f)
    return data


@check_file_exists
def load_yaml(filepath):
    """
    Load a YAML file

    :param filepath: path to yaml file

    """
    return yaml.load(open(filepath), Loader=yaml.FullLoader)


@check_file_exists
def load_volume_file(filepath):
    """
    Load a volume file (e.g., .nii) and returns the data

    :param filepath: path to file
    :param **kwargs: 

    """
    try:
        volume = brainio.load_any(filepath)
    except Exception as e:
        raise ValueError(f"Could not load volume data: {filepath}:\n {e}")
    else:
        return volume


@check_file_exists
def load_mesh_from_file(filepath, *args, **kwargs):
    """	
    Load a a mesh or volume from files like .obj, .stl, ...

    :param filepath: path to file
    :param **kwargs: 

    """
    actor = load(str(filepath))
    color = kwargs.pop("color", None)
    alpha = kwargs.pop("alpha", None)

    if color is not None:
        actor.c(color)
    if alpha is not None:
        actor.alpha(alpha)

    return actor


# ----------------------------- Data manipulation ---------------------------- #
@check_file_exists
def get_probe_points_from_sharptrack(points_filepath, scale_factor=10):
    """
        Loads the location of the of probe points as extracted by SharpTrack
        [https://github.com/cortex-lab/allenCCF].

        :param points_filepath: str, path to a .mat file with probe points
        :param scale_factor: 10, sharptrack uses a 10um reference atlas so the 
                coordinates need to be scaled to match brainrender's
    """
    probe_points = sio.loadmat(points_filepath)
    probe_points = probe_points["pointList"][0][0][0][0][0]
    probe_points_df = pd.DataFrame(
        dict(
            x=probe_points[:, 2] * scale_factor,
            y=probe_points[:, 1] * scale_factor,
            z=probe_points[:, 0] * scale_factor,
        )
    )
    return probe_points_df
