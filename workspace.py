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


# Get the filepath of the JSON file
neurons_file = "Examples/example_files/one_neuron.json"

# Create the 3D models of the neurons
neurons = render_neurons(neurons_file, color_neurites=True, axon_color="antiquewhite", 
                                soma_color="darkgoldenrod", dendrites_color="firebrick")

# then use the "add_neurons" function (and don't forget to render it!)
scene.add_neurons(neurons)
scene.edit_neurons(axon_color="red")
scene.render()


scene.render(interactive=True)

# scene.export_scene()