import os
from random import choice
import pandas as pd
import numpy as np
import random
import json


from brainrender.scene import Scene, MultiScene
from brainrender import *
from brainrender.colors import get_n_shades_of
from brainrender.atlases.aba import ABA
from brainrender.Utils.data_io import listdir

from morphapi.morphology.morphology import Neuron
from morphapi.api.mouselight import MouseLightAPI

def test_imports():
    aba = ABA()
    mlapi = MouseLightAPI()


def test_regions():
    scene = Scene()
    regions = ["MOs", "VISp", "ZI"]
    scene.add_brain_regions(regions, colors="green")
    scene.close()




def test_streamlines():
    scene = Scene()


    filepaths, data = scene.atlas.download_streamlines_for_region("CA1")


    scene.add_brain_regions(['CA1'], use_original_color=True, alpha=.2)

    scene.add_streamlines(data, color="darkseagreen", show_injection_site=False)

    scene.render(camera='sagittal', zoom=1, interactive=False)
    scene.close()




def test_neurons():
    scene = Scene()
    
    mlapi = MouseLightAPI()

    # Fetch metadata for neurons with some in the secondary motor cortex
    neurons_metadata = mlapi.fetch_neurons_metadata(filterby='soma', filter_regions=['MOs'])

    # Then we can download the files and save them as a .json file
    neurons =  mlapi.download_neurons(neurons_metadata[:5])

    scene = Scene(title='One color')
    scene.add_neurons(neurons, color='salmon', display_axon=True, neurite_radius=6)
    scene.render(interactive=False)
    scene.close()



def test_tractography():
    scene = Scene()
    analyzer = ABA()
    p0 = scene.get_region_CenterOfMass("ZI")
    tract = analyzer.get_projection_tracts_to_target(p0=p0)
    scene.add_tractography(tract, display_injection_structure=False, color_by="target_region", 
                                VIP_regions=['MOs'], VIP_color="red", others_color="ivory")

def test_camera():
    # Create a scene
    scene = Scene(camera='top') # specify that you want a view from the top

    # render
    scene.render(interactive=False, )
    scene.close()

    # Now render but with a different view
    scene.render(interactive=False, camera='sagittal', zoom=1)
    scene.close()

    # Now render but with specific camera parameters
    bespoke_camera = dict(
        position = [801.843, -1339.564, 8120.729] ,
        focal = [9207.34, 2416.64, 5689.725],
        viewup = [0.36, -0.917, -0.171],
        distance = 9522.144,
        clipping = [5892.778, 14113.736],
    )

    scene.render(interactive=False, camera=bespoke_camera, zoom=1)
    scene.close()

# def test_connectome():
#     from brainrender.Utils.ABA.volumetric.VolumetricConnectomeAPI import VolumetricAPI

#     vapi = VolumetricAPI(add_root=False, title='Motor cortex projections to ZI')

#     # Get projections from the primary and secondary motor cortices to the zona incerta
#     source = ['MOs', 'MOp']
#     target = 'ZI'
#     vapi.add_mapped_projection(
#                 source, 
#                 target,
#                 cmap='gist_heat', # specify which heatmap to show
#                 alpha=1,
#                 render_target_region=True, # render the targer region
#                 regions_kwargs={
#                             'wireframe':False, 
#                             'alpha':.3, 
#                             'use_original_color':False},
#                 mode='target',
#                 )

def test_labelled_cells():
    # Create a scene
    scene = Scene() # specify that you want a view from the top


    # Gerate the coordinates of N cells across 3 regions
    regions = ["MOs", "VISp", "ZI"]
    N = 1000 # getting 1k cells per region, but brainrender can deal with >1M cells easily. 

    # Render regions
    scene.add_brain_regions(regions, alpha=.2)

    # Get fake cell coordinates
    cells = [] # to store x,y,z coordinates
    for region in regions:
        region_cells = scene.get_n_random_points_in_region(region=region, N=N)
        cells.extend(region_cells)
    x,y,z = [c[0] for c in cells], [c[1] for c in cells], [c[2] for c in cells]
    cells = pd.DataFrame(dict(x=x, y=y, z=z)) 

    # Add cells
    scene.add_cells(cells, color='darkseagreen', res=12, radius=25)



def test_scene_title():
    scene = Scene(title='The thalamus.')


def test_video():
    from brainrender.animation.video import BasicVideoMaker as VideoMaker

    scene = Scene()

    # Create an instance of VideoMaker with our scene
    vm = VideoMaker(scene, niters=10)

    # Make a video!
    vm.make_video(elevation=1, roll=5) # specify how the scene rotates at each frame

