import os
import numpy as np
import pytest
from brainrender.scene import Scene

from brainrender.Utils.camera import get_camera_params
from brainrender.Utils.data_io import listdir, get_subdirs
from brainrender.Utils.data_manipulation import get_slice_coord
from brainrender.colors import (
    get_random_colormap,
    get_n_shades_of,
    getColor,
    getColorName,
    colorMap,
    check_colors,
)
from brainrender.Utils.actors_funcs import edit_actor


@pytest.fixture
def scene():
    return Scene()


def test_get_camera_params(scene):
    if not isinstance(get_camera_params(scene), dict):
        raise ValueError

    if not isinstance(get_camera_params(camera=scene.plotter.camera), dict):
        raise ValueError


def test_io():
    fld = os.getcwd()
    if not isinstance(listdir(fld), list):
        raise ValueError(f"listdir returned: {listdir(fld)}")
    if not isinstance(get_subdirs(fld), list):
        raise ValueError(f"get_subdirs returned: {get_subdirs(fld)}")


def test_get_slice():
    get_slice_coord([0.0, 100.0], 0.5)


def test_colors():
    if not isinstance(get_random_colormap(), str):
        raise ValueError

    cols = get_n_shades_of("green", 40)
    if not isinstance(cols, list):
        raise ValueError
    if len(cols) != 40:
        raise ValueError

    getColor("orange")
    getColor([1, 1, 1])
    getColor("k")
    getColor("#ffffff")
    getColor(7)
    getColor(-7)

    getColorName("#ffffff")

    cols = colorMap([0, 1, 2])
    if not isinstance(cols, (list, np.ndarray)):
        raise ValueError
    if len(cols) != 3:
        raise ValueError

    c = colorMap(3, vmin=-3, vmax=4)

    check_colors(cols)
    check_colors(c)


def test_edit_actors(scene):
    actor = scene.add_brain_regions("TH")

    edit_actor(
        actor,
        wireframe=True,
        color="red",
        line=True,
        line_kwargs={"lw": 2},
        upsample=True,
        downsample=False,
    )
    edit_actor(
        actor, solid=True, downsample=True, smooth=True,
    )
