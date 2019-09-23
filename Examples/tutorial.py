# basic imports
import sys
sys.path.append('./')
import os


"""
    This tutorial is aimed at showing the basic functionality of BrainRender, more advanced tutorials can be found in other Examples/*.py files. 
"""

# ! ADD HOW TO SET UP FOLDER STRUCTURE FIRST

# Brain render allows for the creation of a "scene" in which to render a number of 3d objects (e.g. brain structures, neurons reconstructions etc.)
# so we first need to import the class Scene and create an instance to it, then we can add stuff to it. 

from BrainRender.scene import Scene
tutorial_scene = Scene()

""" ------------------------------
    MODEL BRAIN REGIONS
        see more details in [neurons.py]
    ------------------------------ """ 

# To add brain regions to our scene, we can use the "add_brain_regions" function. 
# To spicy which brain regions to render, we pass a list of strings, each of which is the acronym that corresponds to the brain region of interest

tutorial_scene.add_brain_regions(['PAG'], colors='red') # add the PAG to our scene

# To visualize our scene, we need to call the 'render' function
# remember to press 'q' to close the render window !q
tutorial_scene.render() 

# To know which brain structures are supported and what their acronyms here, we can print the list
# of structures directly from our scene
tutorial_scene.print_structures()  # Or have a look at all_regions.txt

# we can also render multiple brain regions and only colors the ones we are interested:
# create a new scene
tutorial_scene = Scene()
# display multiple regions and color the "VIP" regions
tutorial_scene.add_brain_regions(['CA1', 'ZI', 'MOs'], colors='green', VIP_regions=['MOs'], VIP_color='red') # add the PAG to our scene
tutorial_scene.render() 


""" ------------------------------
    MODEL NEURONS
        see more details in [neurons.py]
    ------------------------------ """ 

# We can also visualise neurons reconstructed as part of the Mouse Light project. 
# we need to first download the neurons' data we are interested as JSON from the mouse light
# neurons browser website, and then we can use this file to render the neurons here. 
# in Examples/example_files you can find a couple JSON files to try out. 

# Get the filepath of the JSON file
neurons_file = "Examples/example_files/one_neuron.json"

# Create the 3D models of the neurons
from BrainRender.Utils.mouselight_parser import render_neurons 
neurons, _ = render_neurons(neurons_file, color_neurites=True, axon_color="antiquewhite", soma_color="darkgoldenrod", dendrites_color="firebrick")

# then use the "add_neurons" function (and don't forget to render it!)
tutorial_scene = Scene()
tutorial_scene.add_neurons(neurons)
tutorial_scene.render() 

""" ------------------------------
    TRACTOGRAPHY
        see more details in [tractography.py]
    ------------------------------ """ 

# Finally, BrainRender can be used to render tractography data downloaded from the Allen Brain Atlas mouse Connectome Database.
# Given a brain region of interest, we can download data from experiments whose injections showed projections to our brain region. 
# Then we can render these projections in 3D

# This kind of interctions with the Allen Brain Atlas datasets are handled by the class called ABA
from BrainRender.ABA_analyzer import ABA

analyzer = ABA()
tract = analyzer.get_projection_tracts_to_target("ZI") # Get the projections to the Zona Incerta

# create a new scene. add the projections and render
tutorial_scene = Scene()
tutorial_scene.add_brain_regions(['ZI'], colors='white', alpha=.5) # add the PAG to our scene
tutorial_scene.add_tractography(tract, display_injection_structure=False, color="antiquewhite", color_by="region")
tutorial_scene.render() 



