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

# add tractography
tract = br.get_projection_tracts_to_target("ZI")
scene.add_tractography(tract, display_injection_structure=True, use_region_color=True)


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