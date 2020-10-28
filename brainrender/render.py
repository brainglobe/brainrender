from vedo import Plotter, show, closePlotter
import numpy as np
from datetime import datetime

from brainrender import settings
from .camera import (
    get_camera,
    check_camera_param,
    set_camera,
    get_camera_params,
)


def get_scene_camera(camera, atlas):
    """
        Gets a working camera. 
        In order these alternatives are used:
            - user given camera
            - atlas specific camera
            - default camera
    """
    if camera is None:
        if atlas.default_camera is not None:
            return check_camera_param(atlas.default_camera)
        else:
            return settings.DEFAULT_CAMERA
    else:
        return check_camera_param(camera)


mtx = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])


class Render:
    transform_applied = False
    is_rendered = False

    def __init__(self):
        self.plotter = Plotter(
            size="full" if settings.WHOLE_SCREEN else "auto",
            axes=self._make_axes(),
            pos=(0, 0),
            title="brainrender",
        )

        self.plotter.keyPressFunction = self.keypress

    def _make_axes(self):
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
            When the scene is first rendered, a transform matrix
            is applied to each actor's points to correct orientation
            mismatches: https://github.com/brainglobe/bg-atlasapi/issues/73
        """
        self.transform_applied = True

        # Flip every actor's orientation
        for actor in self.clean_actors + self.labels:
            if not actor._is_transformed:
                actor.mesh.applyTransform(mtx).reverse()
                actor._is_transformed = True

            if actor._needs_silhouette:
                self.actors.append(actor.make_silhouette())

            if actor._needs_label:
                self.labels.extend(actor.make_label(self.atlas))

    def _apply_style(self):
        for actor in self.clean_actors:
            if settings.SHADER_STYLE != "cartoon":
                actor.mesh.lighting(style=settings.SHADER_STYLE)
            else:
                actor.mesh.lighting("off")

    def render(self, interactive=None, camera=None, zoom=1.25):
        # Get camera
        if camera is None:
            camera = get_camera(settings.DEFAULT_CAMERA)
        else:
            camera = check_camera_param(camera)

        if not self.jupyter:
            set_camera(self, camera)

        # Apply axes correction
        self._correct_axes()

        # Apply style
        self._apply_style()

        if self.inset and not self.jupyter:
            self._get_inset()

        # render
        if not self.jupyter:
            show(
                *self.renderables,
                interactive=interactive or settings.INTERACTIVE,
                zoom=zoom,
                bg=settings.BACKGROUND_COLOR,
                axes=self.plotter.axes,
            )
            self.is_rendered = True
        else:
            print(
                "Your scene is ready for rendering, use: `show(scene.renderables)`"
            )

    def close(self):
        closePlotter()

    def export(self):  # as HTML
        pass

    def screenshot(self, name=None, scale=None):
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

    # ---------------------------------------------------------------------------- #
    #                               USER INTERACTION                               #
    # ---------------------------------------------------------------------------- #
    def keypress(self, key):
        if key == "s":
            self.screenshot()

        elif key == "q" or key == "Esc":
            self.close()

        elif key == "c":
            print(f"Camera parameters:\n{get_camera_params(scene=self)}")
