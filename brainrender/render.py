from vedo import settings as vedosettings
from vedo import Plotter, show, closePlotter
import datetime
import warnings

from pathlib import Path
import brainrender
from brainrender.Utils.scene_utils import (
    get_scene_camera,
    get_scene_plotter_settings,
)
from brainrender.Utils.camera import (
    check_camera_param,
    set_camera,
    get_camera_params,
)

"""
    The render class expands scene.Scene's functionality
    to take care of the rendering and visualization
    of all actors added a scene. 
"""


class Render:
    def __init__(
        self,
        verbose,
        display_inset,
        camera,
        screenshot_kwargs,
        use_default_key_bindings,
    ):
        """
            Creates and manages a Plotter instance

            :param add_root: if False a rendered outline of the whole brain is added to the scene (default value None)
            :param verbose: if False less feedback is printed to screen (default value True)
            :param display_inset: if False the inset displaying the brain's outline is not rendered (but the root is added to the scene) (default value None)
            :param camera: name of the camera parameters setting to use (controls the orientation of the rendered scene)
            :param screenshot_kwargs: pass a dictionary with keys:
                        - 'folder' -> str, path to folder where to save screenshots
                        - 'name' -> str, filename to prepend to screenshots files
            :param use_default_key_bindings: if True the defualt keybindings from vedo are used, otherwise
                            a custom function that can be used to take screenshots with the parameter above. 
        """
        # Setup a few rendering options
        self.verbose = verbose
        self.display_inset = (
            display_inset
            if display_inset is not None
            else brainrender.DISPLAY_INSET
        )

        if vedosettings.notebookBackend == "k3d":
            self.jupyter = True
        else:
            self.jupyter = False

        if self.display_inset and self.jupyter:
            print(
                "Setting 'display_inset' to False as this feature is not \
                            available in juputer notebooks"
            )
            self.display_inset = False

        # Camera parameters
        self.camera = get_scene_camera(camera, self.atlas)

        # Create vedo plotter
        self.plotter = Plotter(**get_scene_plotter_settings(self.jupyter))

        # SCreenshots and keypresses variables
        self.screenshots_folder = Path(
            screenshot_kwargs.pop("folder", self.atlas.output_screenshots)
        )
        self.screenshots_name = screenshot_kwargs.pop(
            "name", brainrender.DEFAULT_SCREENSHOT_NAME
        )

        if not use_default_key_bindings:
            self.plotter.keyPressFunction = self.keypress
            self.verbose = False

        if not brainrender.SCREENSHOT_TRANSPARENT_BACKGROUND:
            vedosettings.screenshotTransparentBackground = False
            vedosettings.useFXAA = True

    def apply_render_style(self):
        if brainrender.SHADER_STYLE is None:  # No style to apply
            return

        for actor in self.actors:
            if actor is not None:
                try:
                    if brainrender.SHADER_STYLE != "cartoon":
                        actor.lighting(style=brainrender.SHADER_STYLE)
                    else:
                        actor.lighting("off")
                except AttributeError:
                    pass  # Some types of actors such as Text 2D don't have this attribute!

    def render(
        self, interactive=True, video=False, camera=None, zoom=None, **kwargs
    ):
        """
        Takes care of rendering the scene
        """
        self.apply_render_style()

        if not video:
            if (
                not self.jupyter
            ):  # cameras work differently in jupyter notebooks?
                if camera is None:
                    camera = self.camera

                if isinstance(
                    camera, (str, dict)
                ):  # otherwise assume that it's vtk.camera
                    camera = check_camera_param(camera)

                set_camera(self, camera)

            if interactive:
                if self.verbose and not self.jupyter:
                    print(brainrender.INTERACTIVE_MSG)
                elif self.jupyter:
                    print(
                        "The scene is ready to render in your jupyter notebook"
                    )
                else:
                    print("\n\nRendering scene.\n   Press 'q' to Quit")

            self._get_inset()

        if zoom is None and not video:
            zoom = 1.85 if brainrender.WHOLE_SCREEN else 1.5

        # Make mesh labels follow the camera
        if not self.jupyter:
            for txt in self.actors_labels:
                txt.followCamera(self.plotter.camera)

        self.is_rendered = True

        args_dict = dict(
            interactive=interactive,
            zoom=zoom,
            bg=brainrender.BACKGROUND_COLOR,
            axes=self.plotter.axes,
        )

        if video:
            args_dict["offscreen"] = True
        show(*self.actors, *self.actors_labels, **args_dict)

    def close(self):
        closePlotter()

    def export_for_web(self, filepath="brexport.html"):
        """
            This function is used to export a brainrender scene
            for hosting it online. It saves an html file that can
            be opened in a web browser to show an interactive brainrender scene
        """
        if not filepath.endswith(".html"):
            raise ValueError("Filepath should point to a .html file")

        # prepare settings
        vedosettings.notebookBackend = "k3d"

        # Create new plotter and save to file
        plt = Plotter()
        plt.add(self.actors)
        plt = plt.show(interactive=False)
        plt.camera[-2] = -1

        print(
            "Ready for exporting. Exporting scenes with many actors might require a few minutes"
        )
        with open(filepath, "w") as fp:
            fp.write(plt.get_snapshot())

        print(
            f"The brainrender scene has been exported for web. The results are saved at {filepath}"
        )

        # Reset settings
        vedosettings.notebookBackend = None
        self.jupyter = False

    # ---------------------------------------------------------------------------- #
    #                               USER INTERACTION                               #
    # ---------------------------------------------------------------------------- #
    def keypress(self, key):
        if key == "s":
            self.take_screenshot()

        elif key == "q":
            self.close()

        elif key == "c":
            print(f"Camera parameters:\n{get_camera_params(scene=self)}")

    def take_screenshot(self):
        if not self.is_rendered:
            print(
                "You need to render the scene before you can take a screenshot"
            )
            return

        if brainrender.SCREENSHOT_TRANSPARENT_BACKGROUND:
            warnings.warn(
                "BRAINRENDER - settings: screenshots are set to have transparent background. Set the parameter 'SCREENSHOT_TRANSPARENT_BACKGROUND' to False if you'd prefer a not transparent background"
            )

        self.screenshots_folder.mkdir(exist_ok=True)

        savename = str(self.screenshots_folder / self.screenshots_name)
        savename += f'_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'

        print(f"\nSaving screenshot at {savename}\n")
        self.plotter.screenshot(filename=savename)
        return savename
