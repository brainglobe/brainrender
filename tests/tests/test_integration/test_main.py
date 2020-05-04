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
from brainrender.Utils.parsers.streamlines import *
from brainrender.Utils.parsers.mouselight import NeuronsParser
from brainrender.Utils.data_io import listdir
from brainrender.Utils.MouseLightAPI.mouselight_info import *
from brainrender.Utils.MouseLightAPI.mouselight_api import MouseLightAPI
from brainrender.Utils.MouseLightAPI.mouselight_info import mouselight_api_info, mouselight_fetch_neurons_metadata
from brainrender.Utils.AllenMorphologyAPI.AllenMorphology import AllenMorphology


def test_imports():
    aba = ABA()
    mlapi = MouseLightAPI()


def test_regions():
    scene = Scene()
    regions = ["MOs", "VISp", "ZI"]
    scene.add_brain_regions(regions, colors="green")

def test_streamlines():
    scene = Scene()


    filepaths, data = scene.atlas.download_streamlines_for_region("CA1")


    scene.add_brain_regions(['CA1'], use_original_color=True, alpha=.2)

    scene.add_streamlines(data, color="darkseagreen", show_injection_site=False)

    scene.render(camera='sagittal', zoom=1)


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

def test_neurons_swc():
    am = AllenMorphology()
    neuron = am.download_neurons(am.neurons.id.values[0:3])
    am.add_neuron(neuron)


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

def test_morphology():
    from brainrender.Utils.AllenMorphologyAPI.AllenMorphology import AllenMorphology

    am = AllenMorphology(scene_kwargs={'title':'A single neuron.'})

    print(am.neurons.head()) # this dataframe has metadata for all available neurons

    neurons = am.download_neurons(am.neurons.id.values[0]) # download one neruons

    # Render 
    am.add_neuron(neurons, color='salmon')

def test_mouselight():
    from brainrender.Utils.MouseLightAPI.mouselight_api import MouseLightAPI
    from brainrender.Utils.MouseLightAPI.mouselight_info import mouselight_api_info, mouselight_fetch_neurons_metadata

    # Fetch metadata for neurons with some in the secondary motor cortex
    neurons_metadata = mouselight_fetch_neurons_metadata(filterby='soma', filter_regions=['MOs'])

    # Then we can download the files and save them as a .json file
    ml_api = MouseLightAPI() 
    neurons_files =  ml_api.download_neurons(neurons_metadata[:2]) # just saving the first couple neurons to speed things up

    # Show neurons and ZI in the same scene:
    scene = Scene()
    scene.add_neurons(neurons_files, soma_color='orangered', dendrites_color='orangered', 
                    axon_color='darkseagreen', neurite_radius=8) # add_neurons takes a lot of arguments to specify how the neurons should look
    # make sure to check the source code to see all available optionsq

    scene.add_brain_regions(['MOs'], alpha=0.15) 
    scene.render(interactive=False, camera='coronal') 
    scene.close()


def test_scene_title():
    scene = Scene(title='The thalamus.')
    scene.add_brain_regions(['TH'], alpha=.4)

def test_streamlines():
    # Start by creating a scene with the allen brain atlas atlas
    scene = Scene()


    # Download streamlines data for injections in the CA1 field of the hippocampus
    filepaths, data = scene.atlas.download_streamlines_for_region("CA1")


    scene.add_brain_regions(['CA1'], use_original_color=True, alpha=.2)

    # you can pass either the filepaths or the data
    scene.add_streamlines(data, color="darkseagreen", show_injection_site=False)
    scene.render(interactive=False, camera='sagittal', zoom=1)
    scene.close()

def test_tractography():
    from brainrender.atlases.aba import ABA
    # Create a scene
    scene = Scene()

    # Get the center of mass of the region of interest
    p0 = scene.get_region_CenterOfMass("ZI")

    # Get projections to that point
    analyzer = ABA()
    tract = analyzer.get_projection_tracts_to_target(p0=p0)

    # Add the brain regions and the projections to it
    scene.add_brain_regions(['ZI'], alpha=.4, use_original_color=True)
    scene.add_tractography(tract, display_injection_structure=False, color_by="region")

    scene.render(interactive=False, )
    scene.close()

def test_video():
    from brainrender.animation.video import BasicVideoMaker as VideoMaker

    scene = Scene()

    # Create an instance of VideoMaker with our scene
    vm = VideoMaker(scene, niters=10)

    # Make a video!
    vm.make_video(elevation=1, roll=5) # specify how the scene rotates at each frame


def test_ibdb():
    from brainrender.atlases.insects_brains_db import IBDB 
    
    scene = Scene(atlas=IBDB,
                atlas_kwargs=dict(species='Schistocerca gregaria'
                ))

    central_complex = ['CBU-S2']
    scene.add_brain_regions(central_complex, alpha=1)

    scene.render() 
    scene.close()