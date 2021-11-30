from vedo import Plotter
from vedo import settings as vsettings
import numpy as np
from datetime import datetime
from rich import print
from pathlib import Path
from myterial import orange, amber, deep_purple_light, teal
from rich.syntax import Syntax
from loguru import logger

from brainrender import settings
from brainrender.camera import (
    get_camera,
    check_camera_param,
    set_camera,
    get_camera_params,
)
from brainrender.actors.points import PointsDensity


# mtx used to transform meshes to sort axes orientation
mtx = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]


class Render:
    is_rendered = False
    plotter = None

    axes_names = ("AP", "DV", "LR")
    axes_lookup = {"x": "AP", "y": "DV", "z": "LR"}
    axes_indices = {"AP": 0, "DV": 1, "LR": 2}

    def __init__(self, plotter=None):
        """
        Backend for Scene, handles all rendering and exporting
        related tasks.
        """
        if plotter is None:
            self._get_plotter()
        else:
            self.plotter = plotter
            self.plotter.keyPressFunction = self.keypress

    def _get_plotter(self):
        """
        Make a vedo plotter with
        fancy axes and all
        """
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
        z_range = np.array([-atlas_shape[2], 0])
        z_ticks = [
            (-v, str(np.abs(v).astype(np.int32)))
            for v in np.linspace(
                0,
                atlas_shape[ax_idx],
                10,
            )
        ]

        if self.atlas.atlas_name == "allen_human_500um":
            z_range = None
            z_ticks = None
            logger.debug(
                "RENDER: manually forcing axes size for human atlas, atlas needs fixing"
            )

        # make custom axes dict
        axes = dict(
            axesLineWidth=3,
            tipSize=0,
            xtitle="AP (μm)",
            ytitle="DV (μm)",
            ztitle="LR (μm)",
            textScale=0.8,
            xTitleRotation=180,
            zrange=z_range,
            zValuesAndLabels=z_ticks,
            xyGrid=False,
            yzGrid=False,
            zxGrid=False,
            xUseBounds=True,
            yUseBounds=True,
            zUseBounds=True,
            xLabelRotation=180,
            yLabelRotation=180,
            zLabelRotation=90,
        )

        return axes

    def _prepare_actor(self, actor):
        """
        When an actor is first rendered, a transform matrix
        is applied to its points to correct axes orientation
        mismatches: https://github.com/brainglobe/bg-atlasapi/issues/73

        Once an actor is 'corrected' it spawns labels and silhouettes as needed
        """
        # don't apply transforms to points density actors
        if isinstance(actor, PointsDensity):
            logger.debug(
                f'Not transforming actor "{actor.name} (type: {actor.br_class})"'
            )
            actor._is_transformed = True

        # Flip every actor's orientation
        if not actor._is_transformed:
            try:
                actor._mesh = actor.mesh.clone()
                actor._mesh.applyTransform(mtx)
            except AttributeError:  # some types of actors dont trasform
                logger.debug(
                    f'Failed to transform actor: "{actor.name} (type: {actor.br_class})"'
                )
                actor._is_transformed = True
            else:
                try:
                    actor.mesh.reverse()
                except AttributeError:  # Volumes don't have reverse
                    logger.debug(
                        f'Failed to reverse actor: "{actor.name} (type: {actor.br_class})"'
                    )
                    pass
                actor._is_transformed = True

        # Add silhouette and labels
        if actor._needs_silhouette and not self.backend:
            self.plotter.add(actor.make_silhouette().mesh)

        if actor._needs_label and not self.backend:
            self.labels.extend(actor.make_label(self.atlas))

    def _apply_style(self):
        """
        Sets the rendering style for each mesh
        """
        for actor in self.clean_actors:
            if settings.SHADER_STYLE != "cartoon":
                style = settings.SHADER_STYLE
            else:
                if self.backend:  # notebook backend
                    print(
                        'Shader style "cartoon" cannot be used in a notebook'
                    )
                style = "off"

            try:
                actor.mesh.reverse()  # flip normals
                actor.mesh.lighting(style=style)

                actor._mesh.reverse()
                actor._mesh.lighting(style=style)
            except AttributeError:
                pass

    def render(
        self,
        interactive=None,
        camera=None,
        zoom=None,
        update_camera=True,
        **kwargs,
    ):
        """
        Renders the scene.

        :param interactive: bool. If note settings.INTERACTIVE is used.
            If true the program's execution is stopped and users
            can interact with scene.
        :param camera: str, dict. If none the default camera is used.
            Pass a valid camera input to specify the camera position when
            the scene is rendered.
        :param zoom: float, if None atlas default is used
        :param update_camera: bool, if False the camera is not changed
        :param kwargs: additional arguments to pass to self.plotter.show
        """
        logger.debug(
            f"Rendering scene. Interactive: {interactive}, camera: {camera}, zoom: {zoom}"
        )
        # get zoom
        zoom = zoom or self.atlas.zoom

        # get vedo plotter
        if self.plotter is None:
            self._get_plotter()

        # Get camera
        camera = camera or settings.DEFAULT_CAMERA
        if isinstance(camera, str):
            camera = get_camera(camera)
        else:
            camera = check_camera_param(camera)

        if "focalPoint" not in camera.keys() or camera["focalPoint"] is None:
            camera["focalPoint"] = self.root._mesh.centerOfMass()

        if not self.backend and camera is not None:
            camera = set_camera(self, camera)

        # Apply axes correction
        for actor in self.clean_actors:
            if not actor._is_transformed:
                self._prepare_actor(actor)
                self.plotter.add(actor.mesh)

            if actor._needs_silhouette or actor._needs_label:
                self._prepare_actor(actor)

        # add labels to the scene
        for label in self.labels:
            if label._is_added:
                continue
            else:
                label._mesh = label.mesh.clone()
                self._prepare_actor(label)
                self.plotter.add(label._mesh.reverse())
                label._is_added = True

        # Apply style
        self._apply_style()

        if self.inset and not self.is_rendered:
            self._get_inset()

        # render
        self.is_rendered = True
        if not self.backend:  # not running in a python script
            if interactive is None:
                interactive = settings.INTERACTIVE

            self.plotter.show(
                interactive=interactive,
                zoom=zoom,
                bg=settings.BACKGROUND_COLOR,
                camera=camera.copy() if update_camera else None,
                interactorStyle=0,
                rate=40,
            )
        elif self.backend == "k3d":  # pragma: no cover
            # Remove silhouettes
            self.remove(*self.get_actors(br_class="silhouette"))
            print(
                f"[{teal}]Your scene is ready for rendering, use:\n",
                Syntax("from vedo import show", lexer_name="python"),
                Syntax("vedo.show(*scene.renderables)", lexer_name="python"),
                sep="\n",
            )
        else:  # pragma: no cover
            print(
                f"[{teal}]Your scene is ready for rendering, use:\n",
                Syntax("from itkwidgets import view", lexer_name="python"),
                Syntax(
                    "view(scene.plotter.show(*scene.renderables))",
                    lexer_name="python",
                ),
                sep="\n",
            )

    def close(self):
        self.plotter.close()

    def export(self, savepath):
        """
        Exports the scene to a .html
        file for online renderings.

        :param savepath: str, Path to a .html file to save the export
        """
        logger.debug(f"Exporting scene to {savepath}")
        _backend = self.backend

        if not self.is_rendered:
            self.render(interactive=False)

        path = Path(savepath)
        if path.suffix != ".html":
            raise ValueError("Savepath should point to a .html file")

        # prepare settings
        vsettings.notebookBackend = "k3d"

        # Create new plotter and save to file
        plt = Plotter()
        plt.add(self.clean_renderables, render=False)
        plt = plt.show(interactive=False)
        plt.camera[-2] = -1

        with open(path, "w") as fp:
            fp.write(plt.get_snapshot())

        print(
            f"The brainrender scene has been exported for web. The results are saved at {path}"
        )

        # Reset settings
        vsettings.notebookBackend = None
        self.backend = _backend

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
        logger.debug(f"Saving scene at {savepath}")
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
