from BrainRender.ABA_analyzer import ABA
from BrainRender.scene import Scene
from BrainRender.settings import *
from BrainRender.Utils.mouselight_parser import render_neurons
import os

from vtkplotter import settings

useParallelProjection = True
useFXAA = True
useDepthPeeling  = True


# get vars to populate test scene
br = ABA()

# makes scene
scene = Scene()


# get the CoM of CA1 and draw a sphere there

scene.add_brain_regions(['PPN'], alpha=.5)
# CA1_CoM = scene.get_region_CenterOfMass("PAG", unilateral=False)
# scene.add_sphere_at_point(pos=CA1_CoM, color="red", radius=500)


# add tractography

# p0 = scene.get_region_CenterOfMass("PPN")
# tract = br.get_projection_tracts_to_target(p0=p0)
# scene.add_tractography(tract, display_injection_structure=False, color="red", color_by="region", )

out_of_pag = br.get_projection_tracts_from_target("PAG")
to_pag =  br.get_projection_tracts_to_target("PAG")
scene.add_tractography(out_of_pag, display_injection_structure=False, color="red", color_by="manual", )
scene.add_tractography(to_pag, display_injection_structure=False, color="green", color_by="manual", )

scene.render(interactive=True)

# scene.export_scene()