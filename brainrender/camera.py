import vtk

from .cameras import cameras


def get_camera(camera):
    return cameras[camera]


def check_camera_param(camera):
    if isinstance(camera, str):
        return get_camera(camera)

    elif not isinstance(camera, dict):
        raise ValueError(
            "Camera should be either a string with a camera name or a dictionary of camera params."
        )

    else:
        params = ["position", "focal", "viewup", "distance", "clipping"]
        for param in params:
            if param not in list(camera.keys()):
                raise ValueError(
                    f"Camera parameters dict should include the following keys: {params}"
                )
        return camera


def set_camera_params(camera, params):
    # Apply camera parameters
    camera.SetPosition(params["position"])
    camera.SetFocalPoint(params["focal"])
    camera.SetViewUp(params["viewup"])
    camera.SetDistance(params["distance"])
    camera.SetClippingRange(params["clipping"])


def set_camera(scene, camera):
    """
        Sets the position of the camera of a brainrender scene.

        :param scene: instance of Scene()
        :param camera: either a string with the name of one of the available cameras, or
                        a dictionary of camera parameters. 
        
    """
    if camera is None:
        return

    if not isinstance(camera, vtk.vtkCamera):
        # Get camera params
        camera = check_camera_param(camera)

        # set params
        set_camera_params(scene.plotter.camera, camera)
    else:
        scene.plotter.camera = camera
    return camera


def get_camera_params(scene=None, camera=None):
    """
        Given an active brainrender scene, it return
        the camera parameters. 
    """

    def clean(val):
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
        position=clean(cam.GetPosition()),
        focal=clean(cam.GetFocalPoint()),
        viewup=clean(cam.GetViewUp()),
        distance=clean(cam.GetDistance()),
        clipping=clean(cam.GetClippingRange()),
        orientation=clean(cam.GetOrientation()),
    )
    return params
