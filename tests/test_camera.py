from brainrender import Scene
from brainrender.camera import (
    get_camera,
    check_camera_param,
    set_camera_params,
    set_camera,
    get_camera_params,
)
import pytest

cameras = [
    "sagittal",
    "sagittal2",
    "frontal",
    "top",
    "top_side",
    "three_quarters",
]


def test_get_camera():
    for camera in cameras:
        get_camera(camera)

    with pytest.raises(KeyError):
        get_camera("nocamera")


def test_camera_params():
    for camera in cameras:
        check_camera_param(camera)


def test_get_camera_params():
    s = Scene()
    s.render(interactive=False)
    cam = s.plotter.camera

    params = get_camera_params(scene=s)
    params2 = get_camera_params(camera=cam)

    check_camera_param(params)
    check_camera_param(params2)


def test_set_camera_params():
    s = Scene()
    params = get_camera_params(scene=s)

    set_camera_params(s.plotter.camera, params)


def test_set_camera():
    s = Scene()
    s.render(interactive=False)
    cam = s.plotter.camera

    set_camera(s, cam)
    set_camera(s, "sagittal")
