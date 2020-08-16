import vtk

sagittal_camera = dict(
    position=[5532.562, 8057.256, 66760.941],
    focal=[6587.835, 3849.085, 5688.164],
    viewup=[0.045, -0.997, 0.061],
    distance=24893.917,
    clipping=[9826.898, 43920.235],
)

sagittal_camera2 = dict(
    position=(10705.845660949382, 7435.678067378925, -36936.3695486442),
    focal=(6779.790352916297, 3916.3916231239214, 5711.389387062087),
    viewup=(-0.0050579179155257475, -0.9965615097647067, -0.08270172139591858),
    distance=42972.44034956088,
    clipping=(30461.81976236306, 58824.38622122339),
)


coronal_camera = dict(
    position=[-54546.708, 526.426, 6171.914],
    focal=[6587.835, 3849.085, 5688.164],
    viewup=[0.054, -0.999, -0.002],
    distance=61226.68,
    clipping=[47007.899, 79272.88],
)

top_camera = dict(
    position=[1482.128, -57162.314, 5190.803],
    focal=[6587.835, 3849.085, 5688.164],
    viewup=[-0.996, 0.083, 0.016],
    distance=61226.68,
    clipping=[52067.13, 72904.35],
)


three_quarters_camera = dict(
    position=[-27271.044, -18212.523, 51683.47],
    focal=[6587.835, 3849.085, 5688.164],
    viewup=[0.341, -0.921, -0.19],
    distance=61226.68,
    clipping=[42904.747, 84437.903],
)

cameras = dict(
    sagittal=sagittal_camera,
    sagittal2=sagittal_camera2,
    coronal=coronal_camera,
    top=top_camera,
    three_quarters=three_quarters_camera,
)


def check_camera_param(camera):
    if isinstance(camera, str):
        if camera not in cameras.keys():
            raise ValueError(
                f"Camera name {camera} if not recognized.\nValid cameras: {cameras.keys()}"
            )
        cam = cameras[camera]
        if not len(cam):
            raise ValueError(f"Camera name {camera} is an empty dictionary!")
        return cam

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


def buildcam(cm):
    """
        Builds a camera from a dictionary of parameters, from vedo
    """

    cm = cm.copy()

    cm_pos = cm.pop("position", None)
    cm_focalPoint = cm.pop("focal", None)
    cm_viewup = cm.pop("viewup", None)
    cm_distance = cm.pop("distance", None)
    cm_clippingRange = cm.pop("clipping", None)
    cm_parallelScale = cm.pop("parallelScale", None)
    cm_thickness = cm.pop("thickness", None)
    cm_viewAngle = cm.pop("viewAngle", None)

    cm = vtk.vtkCamera()

    if cm_pos is not None:
        cm.SetPosition(cm_pos)
    if cm_focalPoint is not None:
        cm.SetFocalPoint(cm_focalPoint)
    if cm_viewup is not None:
        cm.SetViewUp(cm_viewup)
    if cm_distance is not None:
        cm.SetDistance(cm_distance)
    if cm_clippingRange is not None:
        cm.SetClippingRange(cm_clippingRange)
    if cm_parallelScale is not None:
        cm.SetParallelScale(cm_parallelScale)
    if cm_thickness is not None:
        cm.SetThickness(cm_thickness)
    if cm_viewAngle is not None:
        cm.SetViewAngle(cm_viewAngle)

    return cm


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
    if scene is not None:
        if not scene.is_rendered:
            scene.render(interactive=False)
            scene.close()
        cam = scene.plotter.camera
    else:
        cam = camera

    params = dict(
        position=cam.GetPosition(),
        focal_point=cam.GetFocalPoint(),
        view_up=cam.GetViewUp(),
        distance=cam.GetDistance(),
        clipping_range=cam.GetClippingRange(),
        orientation=cam.GetOrientation(),
    )

    return params
