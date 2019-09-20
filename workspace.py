from Renderer.ABA_analyzer import ABA
from Renderer.scene import Scene
from settings import *
from Utils.mouselight_parser import render_neurons
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

scene.add_brain_regions(['PAG'])
CA1_CoM = scene.get_region_CenterOfMass("PAG", unilateral=False)
scene.add_sphere_at_point(pos=CA1_CoM, color="red", radius=500)


# add tractography
# tract = br.get_projection_tracts_to_target("ZI")
# scene.add_tractography(tract, display_injection_structure=True, color="red", color_by="target_region", 
#                         VIP_regions=["MOs"], VIP_color="red", others_color="white", display_onlyVIP_injection_structure=True)


# add neurons
# neurons_file = os.path.join(neurons_fld, "neurons_in_PAG.json")
# neurons = render_neurons(neurons_file, color_neurites=False, soma_color="r", random_color=True)
# scene.add_neurons(neurons)

# neurons_file = os.path.join(neurons_fld, "neurons_in_ZI.json")
# neurons = render_neurons(neurons_file, color_neurites=False, soma_color="g", random_color=True)
# scene.add_neurons(neurons)

# neurons_file = os.path.join(neurons_fld, "axons_in_PAG.json")
# neurons = render_neurons(neurons_file, color_neurites=False, soma_color="y", random_color=True)
# scene.add_neurons(neurons)

scene.render(interactive=True)

# scene.export_scene()