from vedo import settings as vedosettings
from vedo import Plotter, show, closePlotter, buildRulerAxes
import datetime
import warnings
import numpy as np
from pathlib import Path
from pyinspect.classes import Enhanced

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
from brainrender.Utils.data_manipulation import flatten
from rich import print
from pyinspect._colors import mocassin, orange

"""
    The render class expands scene.Scene's functionality
    to take care of the rendering and visualization
    of all actors added a scene. 
"""

mtx = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])


class Render(Enhanced):
    transform_applied = False

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
                        - "folder" -> str, path to folder where to save screenshots
                        - "name" -> str, filename to prepend to screenshots files
                        - "format" -> str, format of the screenshot
            :param use_default_key_bindings: if True the defualt keybindings from vedo are used, otherwise
                            a custom function that can be used to take screenshots with the parameter above. 
        """
        Enhanced.__init__(self)

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
            if self.verbose:
                print(
                    "Setting 'display_inset' to False as this feature is not \
                                available in juputer notebooks"
                )
            self.display_inset = False

        # Camera parameters
        self.camera = get_scene_camera(camera, self.atlas)

        # Create vedo plotter
        self.plotter = Plotter(
            **get_scene_plotter_settings(
                self.jupyter, self.atlas, self.verbose
            )
        )

        if brainrender.AXES_STYLE == 7 and brainrender.SHOW_AXES:
            self.make_custom_axes = True  # to be made at render
        else:
            self.make_custom_axes = False

        self.screenshot_kwargs = screenshot_kwargs

        if not use_default_key_bindings:
            self.plotter.keyPressFunction = self.keypress
            self.verbose = False

        if not brainrender.SCREENSHOT_TRANSPARENT_BACKGROUND:
            vedosettings.screenshotTransparentBackground = False
            vedosettings.useFXAA = True

    def _make_custom_axes(self):
        """
            When using `ruler` axes (vedy style 7), we need to 
            customize them a little bit, this function takes care of it. 
        """
        raise NotImplementedError(
            "Currently ony AXES_STYLE=1 is supported, sorry"
        )

        # Get plotter and axes color
        plt = self.plotter
        c = (0.9, 0.9, 0.9)
        if np.sum(plt.renderer.GetBackground()) > 1.5:
            c = (0.1, 0.1, 0.1)

        bounds = [
            item for sublist in self.atlas._root_bounds for item in sublist
        ]
        rulax = buildRulerAxes(
            bounds,
            c=c,
            units="μm",
            xtitle="AP - ",
            ytitle="DV - ",
            ztitle="LR - ",
            precision=1,
            labelRotation=0,
            axisRotation=90,
            xycross=False,
        )
        rulax.UseBoundsOff()
        rulax.PickableOff()
        plt.renderer.AddActor(rulax)
        plt.axes_instances[0] = rulax

        return

    def _correct_axes(self):
        """
            When the scene is first rendered, a transform matrix
            is applied to each actor's points to correct orientation
            mismatches: https://github.com/brainglobe/bg-atlasapi/issues/73
        """
        self.transform_applied = True

        # Flip every actor's orientation
        for actor in self.actors:
            try:
                _name = actor.name

                if _name is None:
                    _name = ""
            except AttributeError:
                """ not all scene objects will have a name """
                continue

            # Transform the actors that need to be transform
            try:
                if not actor._is_transformed:
                    actor.mesh.applyTransform(mtx).reverse()
                    actor._is_transformed = True

            except AttributeError:
                pass

        # Make labels
        for actor in self.actors:
            try:
                if actor._needs_label:
                    self.actors_labels.extend(actor.make_label(self.atlas))
            except AttributeError:
                pass

        # Make silhouettes
        silhouettes = []
        for actor in self.actors:
            try:
                if actor._needs_silhouette:
                    silhouettes.append(actor.make_silhouette())
            except AttributeError:
                pass
        self.actors.extend(silhouettes)

    def apply_render_style(self):
        if brainrender.SHADER_STYLE is None:  # No style to apply
            return

        for actor in self.actors + self.actors_labels:
            if actor is not None:
                try:
                    if brainrender.SHADER_STYLE != "cartoon":
                        actor.mesh.lighting(style=brainrender.SHADER_STYLE)
                    else:
                        actor.mesh.lighting("off")
                except AttributeError:
                    pass  # Some types of actors such as Text 2D don't have this attribute!

    def render(
        self, interactive=True, video=False, camera=None, zoom=None, **kwargs
    ):
        """
        Takes care of rendering the scene
        """

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

            if interactive and self.verbose:
                if not self.jupyter:
                    print(
                        f"\n\n[{mocassin}]Rendering scene.\n   Press [{orange}]'q'[/{orange}] to Quit"
                    )
                elif self.jupyter:
                    print(
                        f"[{mocassin}]The scene is ready to render in your jupyter notebook"
                    )

            self._get_inset()

        if zoom is None and not video:
            zoom = 1.2 if brainrender.WHOLE_SCREEN else 1.5

        args_dict = dict(
            interactive=interactive,
            zoom=zoom,
            bg=brainrender.BACKGROUND_COLOR,
            axes=self.plotter.axes,
        )

        if video:
            args_dict["offscreen"] = True

        if self.make_custom_axes:
            self._make_custom_axes()
            self.make_custom_axes = False

        # Correct axes orientations
        self._correct_axes()

        # Make mesh labels follow the camera
        if not self.jupyter:
            for txt in self.actors_labels:
                txt.followCamera(self.plotter.camera)
        self.apply_render_style()

        self.is_rendered = True
        to_render = [
            a.mesh for a in flatten(self.actors) + flatten(self.actors_labels)
        ]
        show(*to_render, **args_dict)

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

        if self.verbose:
            print(
                "Ready for exporting. Exporting scenes with many actors might require a few minutes"
            )
        with open(filepath, "w") as fp:
            fp.write(plt.get_snapshot())

        if self.verbose:
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

    def take_screenshot(
        self, screenshots_folder=None, screenshot_name=None, scale=None
    ):
        """
        :param screenshots_folder: folder where the screenshot will be saved
        :param screenshot_name: name of the saved file
        :param scale: int, upsampling factor over screen resolution. Increase to export
        higher quality images
        """

        if screenshots_folder is None:
            screenshots_folder = Path(
                self.screenshot_kwargs.get(
                    "folder", brainrender.DEFAULT_SCREENSHOT_FOLDER
                )
            )
        screenshots_folder.mkdir(exist_ok=True)

        if screenshot_name is None:
            name = self.screenshot_kwargs.get("name", "screenshot")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_format = self.screenshot_kwargs.get("format", ".png")
            screenshot_name = f"{name}_{timestamp}.{file_format}"

        if not self.is_rendered:
            print(
                "You need to render the scene before you can take a screenshot"
            )
            return

        if brainrender.SCREENSHOT_TRANSPARENT_BACKGROUND:
            warnings.warn(
                "BRAINRENDER - settings: screenshots are set to have transparent background. Set the parameter 'SCREENSHOT_TRANSPARENT_BACKGROUND' to False if you'd prefer a not transparent background"
            )

        savename = str(screenshots_folder / screenshot_name)
        print(f"\nSaving new screenshot at {savename}\n")
        self.plotter.screenshot(filename=savename, scale=scale)
        return savename
