"""Camera utilities for brainrender scenes."""

from loguru import logger
from vtkmodules.vtkRenderingCore import vtkCamera

from brainrender.cameras import cameras
from brainrender.scene import Scene


def get_camera(camera: str) -> dict:
    """
    Return the parameters for a pre-defined camera.

    Parameters
    ----------
    camera
        Name of the pre-defined camera.

    Returns
    -------
    dict
        Camera parameters dictionary.
    """
    return cameras[camera]


def check_camera_param(camera: str | dict) -> dict:
    """
    Check that a dictionary of camera parameters is complete.

    Must have entries: ``["pos", "viewup", "clipping_range"]``.

    Parameters
    ----------
    camera
        Camera name or parameters dictionary.

    Returns
    -------
    dict
        Validated camera parameters dictionary.

    Raises
    ------
    ValueError
        If a required key is missing from the camera dictionary.
    """
    if isinstance(camera, str):
        return get_camera(camera)
    else:
        params = ["pos", "viewup", "clipping_range"]
        for param in params:
            if param not in list(camera.keys()):
                raise ValueError(
                    f"Camera parameters dict should include the following keys: {params}, missing: {param}"
                )
        if "focal_point" not in camera.keys():
            camera["focal_point"] = None
        return camera


def set_camera_params(camera: vtkCamera, params: dict) -> None:
    """
    Set camera parameters.

    Parameters
    ----------
    camera
        Camera object to configure.
    params
        Dictionary of camera parameters with keys ``pos``, ``viewup``,
        ``clipping_range``, and optionally ``focal_point`` and ``distance``.
    """
    logger.debug(f"Setting camera parameters: {params}")
    # Apply camera parameters
    camera.SetPosition(params["pos"])
    camera.SetViewUp(params["viewup"])
    camera.SetClippingRange(params["clipping_range"])

    if "focal_point" in params.keys() and params["focal_point"] is not None:
        camera.SetFocalPoint(params["focal_point"])
    if "distance" in params.keys():
        camera.SetDistance(params["distance"])


def set_camera(
    scene: Scene,
    camera: str | dict | vtkCamera | None,
) -> dict | vtkCamera | None:
    """
    Set the position of the camera of a brainrender scene.

    Parameters
    ----------
    scene
        Instance of brainrender Scene.
    camera
        Pre-defined camera name, a dictionary of camera parameters,
        or a ``vtkCamera`` object. If None, returns immediately.

    Returns
    -------
    dict, vtkCamera, or None
        The applied camera parameters or object, or None if not applied.
    """
    if camera is None:
        return None

    if not isinstance(camera, vtkCamera):
        # Get camera params
        camera = check_camera_param(camera)

        # set params
        try:
            set_camera_params(scene.plotter.camera, camera)
        except AttributeError:
            return None
    else:
        scene.plotter.camera = camera
    return camera


def get_camera_params(
    scene: Scene | None = None, camera: vtkCamera | None = None
) -> dict:
    """
    Return the camera parameters from an active scene or camera object.

    Parameters
    ----------
    scene
        Instance of brainrender Scene whose camera is to be used.
    camera
        Camera object to read parameters from.

    Returns
    -------
    dict
        Camera parameters with keys ``pos``, ``focal_point``, ``viewup``,
        ``distance``, and ``clipping_range``.
    """

    def clean(val: tuple | float) -> tuple | int:
        if isinstance(val, tuple):
            return tuple((round(v) for v in val))
        else:
            return round(val)

    if scene is not None:
        if not scene.is_rendered:
            scene.render(interactive=False)
        cam = scene.plotter.camera
    else:
        cam = camera

    params = dict(
        pos=clean(cam.GetPosition()),
        focal_point=clean(cam.GetFocalPoint()),
        viewup=clean(cam.GetViewUp()),
        distance=clean(cam.GetDistance()),
        clipping_range=clean(cam.GetClippingRange()),
    )
    return params
