import os
from random import choice
import pandas as pd
import numpy as np
import random
import json


from brainrender.scene import Scene, MultiScene
from brainrender import *
from brainrender.colors import get_n_shades_of
from brainrender.Utils.ABA.connectome import ABA
from brainrender.Utils.parsers.streamlines import *
from brainrender.Utils.parsers.mouselight import NeuronsParser
from brainrender.Utils.data_io import listdir
from brainrender.Utils.MouseLightAPI.mouselight_info import *
from brainrender.Utils.MouseLightAPI.mouselight_api import MouseLightAPI
from brainrender.Utils.videomaker import VideoMaker



def test_regions():
    scene = Scene()
    regions = ["MOs", "VISp", "ZI"]
    scene.add_brain_regions(regions, colors="green")

def test_streamlines():
    scene = Scene()
    streamlines_files = listdir("Examples/example_files/streamlines")[:2]
    scene.add_streamlines(streamlines_files, color="green")

def test_neurons():
    scene = Scene()
    mlapi = MouseLightAPI()
    neurons_metadata = mouselight_fetch_neurons_metadata(filterby='soma', filter_regions=['MOs'])
    neurons_files =  mlapi.download_neurons(neurons_metadata[:2])

    parser = NeuronsParser(scene=scene, 
                        color_neurites=True, axon_color="antiquewhite", 
                        soma_color="darkgoldenrod", dendrites_color="firebrick")
    neurons, regions = parser.render_neurons(neurons_files)

    scene.add_neurons(neurons_files, color_neurites=False, random_color="jet", display_axon_regions=False)

def test_tractography():
    scene = Scene()
    analyzer = ABA()
    p0 = scene.get_region_CenterOfMass("ZI")
    tract = analyzer.get_projection_tracts_to_target(p0=p0)
    scene.add_tractography(tract, display_injection_structure=False, color_by="target_region", 
                                VIP_regions=['MOs'], VIP_color="red", others_color="ivory")

def test_rendering():
    scene = Scene()
    scene.render()

