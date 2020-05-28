from brainrender.Utils.ABA.volumetric.VolumetricConnectomeAPI import (
    VolumetricAPI,
)


class InteractiveVolumetric(VolumetricAPI):
    def __init__(
        self,
        target_region,
        *args,
        projection_type="afferent",
        cmap=None,
        **kwargs,
    ):
        if projection_type == "afferent":
            title = f"Projections to {target_region}"
        else:
            title = f"Projections from {target_region}"
        VolumetricAPI.__init__(
            self, *args, scene_kwargs=dict(title=title), **kwargs
        )
        self.cmap = cmap

        # Add brain region
        self.target_region = target_region
        self.scene.add_brain_regions([target_region], alpha=0.4)

        # Get region mesh data
        self.target_region_mesh = self.scene.get_region_unilateral(
            target_region, hemisphere="right"
        )
        self.target_region_bounds = self.target_region_mesh.bounds()

        # The position of the point
        self.target = self.scene.atlas.get_region_CenterOfMass(
            target_region
        )  # initialise with a point in the right hemisphere
        self.target_in_region = True
        self.crosshair = []
        self._move_crosshair()

        # Projection
        self.projection_type = projection_type
        self.lego = None
        self._update_projection()

        # Add sliders
        self.scene.plotter.addSlider2D(
            self.slider_ap,
            self.target_region_bounds[0],
            self.target_region_bounds[1],
            value=self.target[0],
            pos=3,
            title="AP coordinate",
        )

        self.scene.plotter.addSlider2D(
            self.slider_dv,
            self.target_region_bounds[2],
            self.target_region_bounds[3],
            value=self.target[1],
            pos=11,
            title="DV coordinate",
        )

        self.scene.plotter.addSlider2D(
            self.slider_ml,
            self.target_region_bounds[4],
            self.target_region_bounds[5],
            value=self.target[2],
            pos=12,
            title="ML coordinate",
        )

    def _reset_actors(self):
        self.scene.actors["others"] = []

    def _move_crosshair(self):
        old_cross = self.crosshair.copy()

        if self.target_in_region:
            self.crosshair = self.scene.add_crosshair_at_point(self.target)
        else:
            self.crosshair = self.scene.add_crosshair_at_point(
                self.target,
                line_kwargs=dict(alpha=0.25),
                point_kwargs=dict(alpha=0.25),
            )

        for act in self.crosshair:
            self.scene.plotter.add(act)

        for act in old_cross:
            self.scene.plotter.remove(act)

    def _update_projection(self):
        if self.lego is not None:
            self.scene.plotter.remove(self.lego)

        if self.target_in_region:
            if self.projection_type == "afferent":
                func = self.add_mapped_projection_to_point
            else:
                func = self.add_mapped_projection_from_point

            self.lego = func(
                self.target,
                vmin=0.000001,
                show_point=False,
                show_poin_region=False,
                show_crosshair=False,
                cmap=self.cmap,
            )
            self.scene.plotter.add(self.lego)
        else:
            self.lego = None

    def _update(self):
        if self.scene._check_point_in_region(
            self.target, self.target_region_mesh
        ):
            self.target_in_region = True
        else:
            self.target_in_region = False

        self._reset_actors()
        self._move_crosshair()
        self._update_projection()

    def slider_ap(self, widget, event):
        self.target[0] = widget.GetRepresentation().GetValue()
        self._update()

    def slider_dv(self, widget, event):
        self.target[1] = widget.GetRepresentation().GetValue()
        self._update()

    def slider_ml(self, widget, event):
        self.target[2] = widget.GetRepresentation().GetValue()
        self._update()
