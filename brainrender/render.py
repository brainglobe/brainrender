from vedo import Plotter, closePlotter
from vedo import settings as vsettings
import numpy as np
from datetime import datetime
from rich import print
from pathlib import Path
from myterial import orange, amber, deep_purple_light

from brainrender import settings
from brainrender.camera import (
    get_camera,
    check_camera_param,
    set_camera,
    get_camera_params,
)


# mtx used to transform meshes to sort axes orientation
# mtx = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
mtx = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]


class Render:
    transform_applied = False
    is_rendered = False
    plotter = None

    def __init__(self):
        """
            Backend for Scene, handles all rendering and exporting
            related tasks.
        """
        return

    def _get_plotter(self):
        # Make a vedo plotter
        self.plotter = Plotter(
            axes=self._make_axes() if settings.SHOW_AXES else None,
            pos=(0, 0),
            title="brainrender",
            bg=settings.BACKGROUND_COLOR,
            offscreen=settings.OFFSCREEN,
            size="full" if settings.WHOLE_SCREEN else "auto",
        )

        self.plotter.keyPressFunction = self.keypress

    def _make_axes(self):
        """
            Returns a dictionary with axes 
            parameters for the vedo plotter
        """
        ax_idx = self.atlas.space.axes_order.index("frontal")

        # make acustom axes dict
        atlas_shape = np.array(self.atlas.metadata["shape"]) * np.array(
            self.atlas.metadata["resolution"]
        )

        z_ticks = [
            (-v, str(np.abs(v).astype(np.int32)))
            for v in np.linspace(0, atlas_shape[ax_idx], 10,)
        ]

        # make custom axes dict
        axes = dict(
            axesLineWidth=3,
            tipSize=0,
            xtitle="AP (μm)",
            ytitle="DV (μm)",
            ztitle="LR (μm)",
            textScale=0.8,
            xTitleRotation=0,
            xFlipText=True,
            zrange=np.array([-atlas_shape[2], 0]),
            zValuesAndLabels=z_ticks,
            xyGrid=False,
            yzGrid=False,
            zxGrid=False,
        )

        return axes

    def _correct_axes(self):
        """
            When an actor is first rendered, a transform matrix
            is applied to its points to correct axes orientation
            mismatches: https://github.com/brainglobe/bg-atlasapi/issues/73

            Once an actor is 'corrected' it spawns labels and silhouettes as needed
        """
        self.transform_applied = True

        # Flip every actor's orientation
        for actor in self.clean_actors + self.labels:
            if not actor._is_transformed:
                actor.applyTransform(mtx)
                try:
                    actor.reverse()
                except AttributeError:  # Volumes don't have reverse
                    pass
                actor._is_transformed = True

            if actor._needs_silhouette and not self.jupyter:
                self.actors.append(actor.make_silhouette())

            if actor._needs_label and not self.jupyter:
                self.labels.extend(actor.make_label(self.atlas))

    def _apply_style(self):
        """
            Sets the rendering style for each mesh
        """
        for actor in self.clean_actors:
            if settings.SHADER_STYLE != "cartoon":
                style = settings.SHADER_STYLE
            else:
                style = "off"

            try:
                actor.lighting(style=style)
            except AttributeError:
                pass

    def render(self, interactive=None, camera=None, zoom=1.75, **kwargs):
        """
            Renders the scene.

            :param interactive: bool. If note settings.INTERACTIVE is used.
                If true the program's execution is stopped and users
                can interact with scene.
            :param camera: str, dict. If none the default camera is used.
                Pass a valid camera input to specify the camera position when
                the scene is rendered.
            :param zoom: float
            :param kwargs: additional arguments to pass to self.plotter.show
        """
        # get vedo plotter
        if self.plotter is None:
            self._get_plotter()

        # Get camera
        if camera is None:
            camera = get_camera(settings.DEFAULT_CAMERA)
        else:
            camera = check_camera_param(camera)

        if not self.jupyter and camera is not None:
            camera = set_camera(self, camera)

        # Apply axes correction
        self._correct_axes()

        # Apply style
        self._apply_style()

        if self.inset and not self.jupyter and not self.is_rendered:
            self._get_inset()

        # render
        self.is_rendered = True
        if not self.jupyter:
            if interactive is None:
                interactive = settings.INTERACTIVE

            for txt in self.labels:
                txt.followCamera(self.plotter.camera)

            self.plotter.show(
                *self.renderables,
                interactive=interactive,
                zoom=zoom,
                bg=settings.BACKGROUND_COLOR,
                offscreen=settings.OFFSCREEN,
                camera=camera.copy() if camera else None,
                interactorStyle=0,
            )
        else:
            # Remove silhouettes
            self.remove(*self.get_actors(br_class="silhouette"))
            print(
                "Your scene is ready for rendering, use: `vedo.show(*scene.renderables)`"
            )

    def close(self):
        closePlotter()

    def export(self, savepath):
        """
            Exports the scene to a .html
            file for online renderings.

            :param savepath: str, Path to a .html file to save the export
        """
        _jupiter = self.jupyter

        if not self.is_rendered:
            self.render(interactive=False)

        path = Path(savepath)
        if path.suffix != ".html":
            raise ValueError("Savepath should point to a .html file")

        # prepare settings
        vsettings.notebookBackend = "k3d"

        # Create new plotter and save to file
        plt = Plotter()
        plt.add(self.renderables)
        plt = plt.show(interactive=False)
        plt.camera[-2] = -1

        with open(path, "w") as fp:
            fp.write(plt.get_snapshot())

        print(
            f"The brainrender scene has been exported for web. The results are saved at {path}"
        )

        # Reset settings
        vsettings.notebookBackend = None
        self.jupyter = _jupiter

        return str(path)

    def screenshot(self, name=None, scale=None):
        """
            Takes a screenshot of the current view
            and save it to file.
            Screenshots are saved in `screenshots_folder`
            (see Scene)

            :param name: str, name of png file
            :param scale: float, >1 for higher resolution
        """
        if not self.is_rendered:
            self.render(interactive=False)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = name or f"brainrender_screenshot_{timestamp}"
        if ".png" not in name:
            name += ".png"

        scale = scale or settings.SCREENSHOT_SCALE

        print(f"\nSaving new screenshot at {name}\n")
        savepath = str(self.screenshots_folder / name)
        self.plotter.screenshot(filename=savepath, scale=scale)
        return savepath

    def _print_camera(self):
        pms = get_camera_params(scene=self)

        focal = pms.pop("focalPoint", None)
        dst = pms.pop("distance", None)

        names = [
            f"[green bold]     '{k}'[/green bold]: [{amber}]{v},"
            for k, v in pms.items()
        ]
        print(
            f"[{deep_purple_light}]Camera parameters:",
            f"[{orange}]    {{",
            *names,
            f"[{orange}]   }}",
            f"[{deep_purple_light}]Additional, (optional) parameters:",
            f"[green bold]     'focalPoint'[/green bold]: [{amber}]{focal},",
            f"[green bold]     'distance'[/green bold]: [{amber}]{dst},",
            sep="\n",
        )

    def keypress(self, key):  # pragma: no cover
        """
            Hanles key presses for interactive view
            -s: take's a screenshot
            -q: closes the window
            -c: prints the current camera parameters
        """
        if key == "s":
            self.screenshot()

        elif key == "q" or key == "Esc":
            self.close()

        elif key == "c":
            self._print_camera()
