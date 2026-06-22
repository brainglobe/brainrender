"""Scene rendering backend for brainrender."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from loguru import logger
from myterial import teal
from rich import print
from rich.syntax import Syntax
from vedo import Plotter
from vedo import Volume as VedoVolume
from vedo import settings as vsettings

from brainrender import settings
from brainrender.actors.points import PointsDensity
from brainrender.camera import (
    check_camera_param,
    get_camera,
    set_camera,
)

if TYPE_CHECKING:
    from brainrender.actor import Actor

# mtx used to transform meshes to sort axes orientation
mtx = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]
mtx_swap_x_z = [[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]]


class Render:
    is_rendered = False
    plotter = None

    axes_names = ("AP", "DV", "LR")
    axes_lookup = {"x": "AP", "y": "DV", "z": "LR"}
    axes_indices = {"AP": 0, "DV": 1, "LR": 2}

    def __init__(self, plotter: Plotter | None = None) -> None:
        """
        Backend for Scene, handles all rendering and exporting related tasks.

        Parameters
        ----------
        plotter
            Existing vedo Plotter to use. A new one is created if None.
        """
        if plotter is None:
            self._get_plotter()
        else:
            self.plotter = plotter
            self.plotter.keyPressFunction = self.keypress

    def _get_plotter(self) -> None:
        """
        Instantiate a vedo Plotter with custom axes and settings.
        """
        self.plotter = Plotter(
            axes=self._make_axes() if settings.SHOW_AXES else None,
            pos=(0, 0),
            title="brainrender",
            bg=settings.BACKGROUND_COLOR,
            offscreen=settings.OFFSCREEN,
            size="full" if settings.WHOLE_SCREEN else (1600, 1200),
        )

        self.plotter.keyPressFunction = self.keypress

    def _make_axes(self) -> dict:
        """
        Build a custom axes parameter dict for the vedo Plotter.

        Returns
        -------
        dict
            Axes configuration passed directly to vedo.
        """
        ax_idx = self.atlas.space.axes_order.index("frontal")

        # make a custom axes dict
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
            axes_linewidth=3,
            tip_size=0,
            xtitle="AP (μm)",
            ytitle="DV (μm)",
            ztitle="LR (μm)",
            text_scale=0.8,
            xtitle_rotation=180,
            zrange=z_range,
            z_values_and_labels=z_ticks,
            xygrid=False,
            yzgrid=False,
            zxgrid=False,
            x_use_bounds=True,
            y_use_bounds=True,
            z_use_bounds=True,
            xlabel_rotation=180,
            ylabel_rotation=180,
            zlabel_rotation=90,
        )

        return axes

    def _prepare_actor(self, actor: Actor) -> None:
        """
        Apply axis-orientation transform to an actor on first render.

        Corrects axes orientation mismatches (see
        https://github.com/brainglobe/brainglobe-atlasapi/issues/73),
        then spawns any pending labels and silhouettes.

        Parameters
        ----------
        actor
            Actor to prepare.
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

                if isinstance(actor._mesh, VedoVolume):
                    actor._mesh.permute_axes(2, 1, 0)
                    actor._mesh.apply_transform(mtx, True)
                    actor._mesh.transform = (
                        None  # otherwise it gets applied twice
                    )
                elif actor.br_class in ["None", "Gene Data"]:
                    actor._mesh.apply_transform(mtx_swap_x_z)
                    actor._mesh.apply_transform(mtx)
                else:
                    actor._mesh.apply_transform(mtx)

            except AttributeError:  # some types of actors don't transform
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
                actor._is_transformed = True

        # Add silhouette and labels
        if actor._needs_silhouette and not self.backend:
            self.plotter.add(actor.make_silhouette().mesh)

        if actor._needs_label and not self.backend:
            self.labels.extend(actor.make_label(self.atlas))

    def _apply_style(self) -> None:
        """
        Set the rendering style for each mesh.
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
        interactive: bool | None = None,
        camera: str | dict | None = None,
        zoom: float | None = None,
        resetcam: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Render the scene.

        Parameters
        ----------
        interactive
            If None, falls back to ``settings.INTERACTIVE``. When True,
            execution pauses so the user can interact with the scene.
        camera
            Camera name or parameter dict. Falls back to
            ``settings.DEFAULT_CAMERA`` if None.
        zoom
            Camera zoom level. Falls back to the atlas default if None.
        resetcam
            Reset the camera between renders.
        **kwargs
            Additional arguments forwarded to ``self.plotter.show``.
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

        if "focal_point" not in camera.keys() or camera["focal_point"] is None:
            camera["focal_point"] = self.root._mesh.center_of_mass()

        if not self.backend and camera is not None:
            _ = set_camera(self, camera)

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
                rate=40,
                axes=self.plotter.axes,
                resetcam=resetcam,
            )
        elif self.backend == "k3d":  # pragma: no cover
            # Remove silhouettes
            self.remove(*self.get_actors(br_class="silhouette"))
            print(
                f"[{teal}]Your scene is ready for rendering, use:\n",
                Syntax("from vedo import Plotter", lexer="python"),
                Syntax("plt = Plotter()", lexer="python"),
                Syntax("plt.show(*scene.renderables)", lexer="python"),
                sep="\n",
            )
        else:  # pragma: no cover
            print(
                f"[{teal}]Your scene is ready for rendering, use:\n",
                Syntax("from itkwidgets import view", lexer="python"),
                Syntax(
                    "view(scene.plotter.show(*scene.renderables))",
                    lexer="python",
                ),
                sep="\n",
            )

    def close(self) -> None:
        """
        Close the vedo Plotter window.
        """
        self.plotter.close()

    def export(self, savepath: str | Path, **kwargs: Any) -> str:
        """
        Export the scene to a ``.html`` file for online rendering.

        Parameters
        ----------
        savepath
            Path to the output ``.html`` file.
        **kwargs
            Additional arguments forwarded to :meth:`render`.

        Returns
        -------
        str
            Absolute path of the saved file.

        Raises
        ------
        ValueError
            If *savepath* does not have a ``.html`` suffix.
        """
        logger.debug(f"Exporting scene to {savepath}")
        _backend = self.backend
        _default_backend = vsettings.default_backend

        if not self.is_rendered:
            self.render(interactive=False, **kwargs)

        path = Path(savepath)
        if path.suffix != ".html":
            raise ValueError("Savepath should point to a .html file")

        # prepare settings
        vsettings.default_backend = "k3d"

        # Create new plotter and save to file
        plt = Plotter()
        plt.add(self.clean_renderables).render()
        plt = plt.show(interactive=False)

        with open(path, "w") as fp:
            fp.write(plt.get_snapshot())

        print(
            f"The brainrender scene has been exported for web. The results are saved at {path}"
        )

        # Reset settings
        vsettings.default_backend = _default_backend
        self.backend = _backend

        return str(path)

    def screenshot(
        self,
        name: str | None = None,
        scale: float | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Take a screenshot of the current view and save it to file.

        Screenshots are saved in ``screenshots_folder`` (see Scene).

        Parameters
        ----------
        name
            Output filename. Defaults to a timestamped ``.png`` if None.
            Unsupported extensions are silently replaced with ``.png``.
        scale
            Resolution multiplier. Values above 1 increase resolution.
            Falls back to ``settings.SCREENSHOT_SCALE`` if None.
        **kwargs
            Additional arguments forwarded to :meth:`render`.

        Returns
        -------
        str
            Absolute path of the saved screenshot.
        """
        if not self.is_rendered:
            self.render(interactive=False, **kwargs)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = Path(name or f"brainrender_screenshot_{timestamp}")

        # If no suffix is provided or it an unsupported format, default to .png
        if name.suffix not in [".png", ".eps", ".pdf", ".svg", ".jpg"]:
            name = name.with_suffix(".png")

        scale = scale or settings.SCREENSHOT_SCALE

        print(f"\nSaving new screenshot at {name}\n")

        savepath = str(self.screenshots_folder / name)
        logger.debug(f"Saving scene at {savepath}")
        self.plotter.screenshot(filename=savepath, scale=scale)
        return savepath

    def keypress(self, key: str) -> None:  # pragma: no cover
        """
        Handle key presses during interactive rendering.

        - ``s``: take a screenshot
        - ``q`` / ``Esc``: close the window
        - ``c``: print current camera parameters

        Parameters
        ----------
        key
            Key identifier string from vedo.
        """
        if key == "s":
            self.screenshot()

        elif key in ("q", "Esc"):
            self.close()
