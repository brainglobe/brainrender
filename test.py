"""
    Script used to test core functionalities
"""

try:
    from brainrender.scene import Scene, DualScene, RatScene, MultiScene , DrosophilaScene
    from brainrender.variables import *
    from brainrender.colors import get_n_shades_of
    from brainrender.Utils.ABA.connectome import ABA
    from brainrender.Utils.parsers.streamlines import *
    from brainrender.Utils.parsers.mouselight import NeuronsParser
    from brainrender.Utils.data_io import listdir
    from brainrender.Utils.MouseLightAPI.mouselight_info import *
    from brainrender.Utils.MouseLightAPI.mouselight_download_neurons import *
    from brainrender.Utils.videomaker import VideoMaker
except:
    raise ValueError("Failed at imports")

import os
from random import choice
import pandas as pd
import numpy as np
import random
import json


# ! TESTING SCENE CREATION
print("Ceating scene + adding brain rgions")
try:
    scene = Scene()
    regions = ["MOs", "VISp", "ZI"]

    scene.add_brain_regions(regions, colors="green")
except:
    raise ValueError("Failed at SCENE")

# ! TESTING NEURONS RENDERING
print("Rendering neurons")
try:
    neurons_metadata = mouselight_fetch_neurons_metadata(filterby='soma', filter_regions=['MOs'])
    neurons_files =  download_neurons(neurons_metadata[:2])

    parser = NeuronsParser(scene=scene, 
                         color_neurites=True, axon_color="antiquewhite", 
                         soma_color="darkgoldenrod", dendrites_color="firebrick")
    neurons, regions = parser.render_neurons(neurons_files)

    scene.add_neurons(neurons_files, color_neurites=False, random_color="jet", display_axon_regions=True)
except:
    raise ValueError("Failed at NEURONS")

# ! TESTING STREAMLINES
print("Rendering streamlines")
try:
    streamlines_files = listdir("Examples/example_files/streamlines")[:2]
    scene.add_streamlines(streamlines_files, color="green")
except:
    raise ValueError("Failed at STREAMLINES")


# ! TESTING TRACTOGRAPHY
print("Rendering tractography")
try:
    analyzer = ABA()
    p0 = scene.get_region_CenterOfMass("ZI")
    tract = analyzer.get_projection_tracts_to_target(p0=p0)
    scene.add_tractography(tract, display_injection_structure=False, color_by="target_region", 
                                VIP_regions=['MOs'], VIP_color="red", others_color="ivory"
                               )
except:
    raise ValueError("Failed at TRACTOGRAPHY")

# ! TESTING VIDEO
print("Making video")
try:
    vm = VideoMaker(scene, savefile="Output/Videos/video.mp4", niters=25)
    vm.make_video(elevation=1, roll=5)
except:
    raise ValueError("Failed at VIDEO")

# ! TESTING RENDERING
print("Rendering scene")
try:
    scene.render()
except:
    raise ValueError("Failed at rendering")

