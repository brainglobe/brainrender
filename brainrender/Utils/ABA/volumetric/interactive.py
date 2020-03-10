from functools import partial

from brainrender.Utils.ABA.volumetric.VolumetricConnectomeAPI import VolumetricAPI


class InteractiveVolumetric(VolumetricAPI):

    def __init__(self, target_region, *args, projection_type='afferent', **kwargs):
        VolumetricAPI.__init__(self, *args, **kwargs)

        self.projection_type = projection_type
        
        
        self.target_region = target_region
        self.target_region_mesh = self.scene._get_structure_mesh(target_region)
        self.target_region_bounds = self.target_region_mesh.bounds()
        
        self.target = self.scene.get_region_CenterOfMass(target_region) # initialise with a point in the right hemisphere
        self._move_crosshair()

        # Add sliders
        self.scene.plotter.addSlider2D(self.slider_x, self.target_region_bounds[0], self.target_region_bounds[1],
                    value = self.target[0], pos=3, title='X coordinate')

    def _reset_actors(self):
        self.scene.actors['others'] = []

    def _move_crosshair(self):
        self.scene.add_crosshair_at_point(self.target)

    def _update(self):
        self.scene.plotter.show(interactive=0)
        self._reset_actors()
        self._move_crosshair()
        self.scene.plotter.show(interactive=1)
        
    def slider_x(self, widget, event):
        self.target[0] = widget.GetRepresentation().GetValue()
        self._update()

    def slider_y(self, widget, event):
        self.target[1] = widget.GetRepresentation().GetValue()
        self._update()

    def slider_z(self, widget, event):
        self.target[2] = widget.GetRepresentation().GetValue()
        self._update()

