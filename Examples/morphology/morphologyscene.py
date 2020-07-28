""" 
    This tutorial shows how to render a neuron from a .swc file
    with the MorphologyScene class
"""
import brainrender

brainrender.SHADER_STYLE = "cartoon"

from brainrender.morphology.visualise import MorphologyScene


scene = MorphologyScene(title="A neuron")

neuron = scene.add_neurons(
    "Examples/example_files/neuron2.swc",
    color=dict(soma="red", dendrites="orangered", axon=[0.4, 0.4, 0.4],),
    neurite_radius=4,
)

scene.render()
