from Renderer.ABA_analyzer import ABA
from Renderer.scene import Scene
from settings import *
from Utils.mouselight_parser import render_neurons
import os

# get vars to populate test scene
br = ABA()

# makes scene
scene = Scene()

# add tractography
neurons_file = os.path.join(neurons_fld, "neurons_in_ZI.json")

tract = br.get_projection_tracts_to_target("GRN")
scene.add_tractography(tract, display_injection_structure=True, use_region_color=True)

neurons = render_neurons(neurons_file, color_neurites=False, random_color=True)
scene.add_neurons(neurons_file, )

scene.render()