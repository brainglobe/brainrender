from brainrender.scene import Scene
from brainrender.colors import getColor
from brainrender.Utils.camera import get_camera_params
from plotoptix import TkOptiX
from plotoptix.materials import m_thin_walled, m_matt_diffuse
import numpy as np


class RayScene(Scene):
    # Default params
    min_accumulation_step = 4
    max_accumulation_frames = 100
    light_shading = "Hard"

    ambient_light = 0.25

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.optix = TkOptiX()
        self.setup_params()
        self.setup_materials()

    def setup_params(self):
        self.optix.set_param(
            max_accumulation_frames=self.max_accumulation_frames,
            min_accumulation_step=self.min_accumulation_step,
            light_shading=self.light_shading,
        )
        # self.optix.set_uint("path_seg_range", 12, 32)

    def post_processing(self):
        # Denoiser blend allows for different mixing with the raw image. Its value
        # can be modified also during the ray tracing.
        # Note: denoising is applied when > 4 accumulation frames are completed.
        self.optix.set_float("denoiser_blend", 0.25)
        self.optix.add_postproc("Denoiser")

    def setup_materials(self):
        glass = m_thin_walled.copy()
        glass["refraction_index"] = [1.5, 1.5, 1.5]
        self.optix.setup_material("glass", glass)

        # matt_glass = m_matt_glass.copy()
        # matt_glass['vol_scattering'] = 0
        # matt_glass['base_roughness'] = 0
        # self.optix.setup_material("matt_glass", matt_glass)

        self.optix.setup_material("diffuse", m_matt_diffuse)

    def add_actor_as_mesh(self, actor, actor_name=None):
        if actor is None:
            return

        if actor_name is None:
            actor_name = str(int(np.random.uniform(0, 10000)))

        if actor.alpha() < 1:
            mat = "glass"
            color = np.array([c * 25 for c in getColor(actor.color())])
        else:
            mat = "diffuse"
            color = actor.color()

        self.optix.set_mesh(
            actor_name, actor.points(), actor.faces(), c=color, mat=mat
        )

    def render(
        self, *args, show=True, **kwargs,
    ):
        """
            Renders the content of the scene as a RayTracing interactive rendering 
            with plotoptix.TkOptiX. It tries as much as possible to replicate the 
            content and look of standard brainrender scenes
        """
        # render Scene first
        super().render(*args, interactive=False, **kwargs)
        self.close()

        # General scene setting
        self.optix.set_background(getColor(self.plotter.backgrcol))
        self.optix.set_ambient(self.ambient_light)

        # add meshes
        for mesh in self.get_actors():
            self.add_actor_as_mesh(mesh)

        # Set up camera
        camera_params = get_camera_params(self)
        self.optix.setup_camera(
            "cam1", eye=camera_params["position"], up=[0, -1, 0]
        )
        self.optix.camera_fit()
        self.optix.camera_move_by_local(shift=[0, 0, 1000])

        # Set up lights
        d = np.linalg.norm(
            self.optix.get_camera_target() - self.optix.get_camera_eye()
        )
        self.optix.setup_light(
            "light1", color=1, radius=0.3 * d,
        )

        # set up post processing and render
        self.post_processing()

        if show:
            self.optix.start()
