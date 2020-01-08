"""
    Script used to test core functionalities
"""

try:
    from brainrender.scene import Scene, MultiScene
    from brainrender.variables import *
    from brainrender.colors import get_n_shades_of
    from brainrender.Utils.ABA.connectome import ABA
    from brainrender.Utils.parsers.streamlines import *
    from brainrender.Utils.parsers.mouselight import NeuronsParser
    from brainrender.Utils.data_io import listdir
    from brainrender.Utils.MouseLightAPI.mouselight_info import *
    from brainrender.Utils.MouseLightAPI.mouselight_api import MouseLightAPI
    from brainrender.Utils.videomaker import VideoMaker
except Exception as e:
    raise ValueError("Failed at imports: {}".format(e))

import os
from random import choice
import pandas as pd
import numpy as np
import random
import json
import argparse

# Parse arguments
parser = argparse.ArgumentParser(description='Test Brain Render.')
parser.add_argument('-s', "--scene", help="which scene to test", default='all')
args = parser.parse_args()

if args.scene == 'all':
    regions, neurons, streamlines, tractography = True, True, True, True
else:
    regions, neurons, streamlines, tractography = False, False, False, False



scene = Scene()


# ! TESTING SCENE CREATION
if regions or args.scene.lower() == 'regions':
    print("\n\nCeating scene + adding brain rgions")
    try:
        regions = ["MOs", "VISp", "ZI"]

        scene.add_brain_regions(regions, colors="green")
    except Exception as e:
        raise ValueError("Failed at SCENE {}".format(e))

# ! TESTING STREAMLINES
if streamlines or args.scene.lower() == 'streamlines':
    print("\n\nRendering streamlines")
    try:
        streamlines_files = listdir("Examples/example_files/streamlines")[:2]
        scene.add_streamlines(streamlines_files, color="green")
    except Exception as e:
        raise ValueError("Failed at STREAMLINES {}".format(e))



# ! TESTING NEURONS RENDERING
if neurons or args.scene.lower() == 'neurons':
    print("\n\nRendering neurons")
    try:
        mlapi = MouseLightAPI()
        neurons_metadata = mouselight_fetch_neurons_metadata(filterby='soma', filter_regions=['MOs'])
        neurons_files =  mlapi.download_neurons(neurons_metadata[:2])

        parser = NeuronsParser(scene=scene, 
                            color_neurites=True, axon_color="antiquewhite", 
                            soma_color="darkgoldenrod", dendrites_color="firebrick")
        neurons, regions = parser.render_neurons(neurons_files)

        scene.add_neurons(neurons_files, color_neurites=False, random_color="jet", display_axon_regions=False)
    except Exception as e:
        raise ValueError("Failed at NEURONS {}".format(e))


# ! TESTING TRACTOGRAPHY
if tractography or args.scene.lower() == 'tractography':
    print("\n\nRendering tractography")
    try:
        analyzer = ABA()
        p0 = scene.get_region_CenterOfMass("ZI")
        tract = analyzer.get_projection_tracts_to_target(p0=p0)
        scene.add_tractography(tract, display_injection_structure=False, color_by="target_region", 
                                    VIP_regions=['MOs'], VIP_color="red", others_color="ivory"
                                )
    except Exception as e:
        raise ValueError("Failed at TRACTOGRAPHY {}".format(e))


# ! TESTING RENDERING
print("\n\nRendering scene")
try:
    scene.render()
except Exception as e:
    raise ValueError("Failed at rendering {}".format(e))

