sagittal_camera = dict(
    position = [5532.562, 8057.256, 66760.941] ,
    focal = [6587.835, 3849.085, 5688.164],
    viewup = [0.045, -0.997, 0.061],
    distance = 24893.917,
    clipping = [9826.898, 43920.235] ,
)

coronal_camera = dict(
    position = [-54546.708, 526.426, 6171.914] ,
    focal = [6587.835, 3849.085, 5688.164],
    viewup = [0.054, -0.999, -0.002],
    distance = 61226.68,
    clipping = [47007.899, 79272.88] ,
)

top_camera = dict(
    position =  [1482.128, -57162.314, 5190.803] ,
    focal = [6587.835, 3849.085, 5688.164],
    viewup =  [-0.996, 0.083, 0.016],
    distance = 61226.68,
    clipping =  [52067.13, 72904.35] ,
)


three_quarters_camera = dict(
    position = [-27271.044, -18212.523, 51683.47] ,
    focal = [6587.835, 3849.085, 5688.164],
    viewup = [0.341, -0.921, -0.19],
    distance = 61226.68,
    clipping = [42904.747, 84437.903] ,
)

cameras = dict(
    sagittal = sagittal_camera,
    coronal = coronal_camera,
    top = top_camera,
    three_quarters = three_quarters_camera,
)

def check_camera_param(camera):
    if isinstance(camera, str):
        if camera not in cameras.keys():
            raise ValueError(f"Camera name {camera} if not recognized.\nValid cameras: {cameras.keys()}")
        return cameras[camera]
    elif not isinstance(camera, dict):
        raise ValueError(f"Camera should be either a string with a camera name or a dictionary of camera params.")
    else:
        params = ['position', 'focal', 'viewup', 'distance', 'clipping']
        for param in params:
            if param not in list(camera.keys()):
                raise ValueError(f"Camera parameters dict should include the following keys: {params}")
        return camera

def set_camera(scene, camera):
    """
        Sets the position of the camera of a brainrender scene.

        :param scene: instance of Scene()
        :param camera: either a string with the name of one of the available cameras, or
                        a dictionary of camera parameters. 
        
    """
    # Get camera params
    camera = check_camera_param(camera)

    # Apply camera parameters
    scene.plotter.camera.SetPosition(camera['position'])
    scene.plotter.camera.SetFocalPoint(camera['focal'])
    scene.plotter.camera.SetViewUp(camera['viewup'])
    scene.plotter.camera.SetDistance(camera['distance'])
    scene.plotter.camera.SetClippingRange(camera['clipping'])
