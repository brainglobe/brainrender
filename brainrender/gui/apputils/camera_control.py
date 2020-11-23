import brainrender


class CameraControl:
    """
        Collection of functions to implement the actions of buttons
        aimed at controlling the camera of the brainrender Scene
        in the GUI.
    """

    def __init__(self):
        return

    def reset_camera(self):
        self.camera_orientation = brainrender.settings.DEFAULT_CAMERA
        self._update()

    def move_camera_front(self):
        self.camera_orientation = "frontal"  # specify brainrender camera
        self._update()

    def move_camera_top(self):
        self.camera_orientation = "top"  # specify brainrender camera
        self._update()

    def move_camera_side1(self):
        self.camera_orientation = "sagittal"  # specify brainrender camera
        self._update()

    def move_camera_side2(self):
        self.camera_orientation = "sagittal2"  # specify brainrender camera
        self._update()
