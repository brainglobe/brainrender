import brainrender
from loguru import logger
from brainrender.camera import get_camera_params


class CameraControl:
    """
    Collection of functions to implement the actions of buttons
    aimed at controlling the camera of the brainrender Scene
    in the GUI.
    """

    def __init__(self):
        return

    def _update_camera(self):
        if self.camera_orientation is not None:
            camera = self.camera_orientation
            self.camera_orientation = None
        else:
            camera = get_camera_params(scene=self.scene)

        self.scene.render(camera=camera)
        self._update()

        logger.debug(f"GUI: resetting camera to: {self.camera_orientation}")

    def reset_camera(self):
        self.camera_orientation = brainrender.settings.DEFAULT_CAMERA
        self._update_camera()

    def move_camera_front(self):
        self.camera_orientation = "frontal"  # specify brainrender camera
        self._update_camera()

    def move_camera_top(self):
        self.camera_orientation = "top"  # specify brainrender camera
        self._update_camera()

    def move_camera_side1(self):
        self.camera_orientation = "sagittal"  # specify brainrender camera
        self._update_camera()

    def move_camera_side2(self):
        self.camera_orientation = "sagittal2"  # specify brainrender camera
        self._update_camera()
