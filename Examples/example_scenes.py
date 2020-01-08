import sys
sys.path.append("./")
import pandas as pd

from brainrender.scene import Scene
from brainrender import *
from brainrender.Utils.ABA.connectome import ABA

from brainrender.Utils.MouseLightAPI.mouselight_info import mouselight_api_info, mouselight_fetch_neurons_metadata
from brainrender.Utils.MouseLightAPI.mouselight_api import MouseLightAPI

from brainrender.Utils.parsers.streamlines import StreamlinesAPI
from brainrender.Utils.data_io import listdir
from brainrender.colors import get_n_shades_of

aba = ABA()
streamlines_api = StreamlinesAPI()
mlapi = MouseLightAPI()


camera = dict(
    position = [1379.055, -3165.463, 28921.812] ,
    focal = [6919.886, 3849.085, 5688.164],
    viewup = [0.171, -0.954, -0.247],
    distance = 24893.917,
    clipping = [9826.898, 43920.235] ,
)

def set_camera(scene):
    scene.rotated = True
    scene.plotter.camera.SetPosition(camera['position'])
    scene.plotter.camera.SetFocalPoint(camera['focal'])
    scene.plotter.camera.SetViewUp(camera['viewup'])
    scene.plotter.camera.SetDistance(camera['distance'])
    scene.plotter.camera.SetClippingRange(camera['clipping'])



# ---------------------------------------------------------------------------- #
#                   DEFINE A FUNCTION FOR EACH EXAMPLE SCENE                   #
# ---------------------------------------------------------------------------- #

def BrainRegionsScene():
    scene = Scene()
    scene.add_brain_regions(['TH', 'VP'], use_original_color=True, alpha=1)

    act = scene.actors['regions']['TH']
    scene.edit_actors([act], wireframe=True) 

    set_camera(scene)
    scene.render()

# ---------------------------------------------------------------------------- #

def NeuronsScene(show_regions = False):
    scene = Scene()

    fl = 'Examples/example_files/one_neuron.json'
    scene.add_neurons(fl, soma_color='darkseagreen', force_to_hemisphere="right",)

    if show_regions:
        scene.add_brain_regions(['ZI', 'PAG', 'MRN', 'NPC', "VTA", "STN", "PPT", "SCm", "HY"], 
                        use_original_color=True, alpha=.5)

    set_camera(scene)
    scene.render() 

# ---------------------------------------------------------------------------- #

def NeuronsScene2():
    scene = Scene()

    neurons_metadata = mouselight_fetch_neurons_metadata(filterby='soma', filter_regions=['MOp5'])
    neurons_files =  mlapi.download_neurons(neurons_metadata[2:6]) 
    scene.add_neurons(neurons_files, soma_color='deepskyblue', force_to_hemisphere="right")

    streamlines_files, data = streamlines_api.download_streamlines_for_region("MOp") 
    scene.add_streamlines(data[:1], color="palegreen", show_injection_site=False, alpha=.2, radius=10)

    set_camera(scene)
    scene.render()

def NeuronsScene3():
    scene = Scene()

    neurons_metadata = mouselight_fetch_neurons_metadata(filterby='soma', filter_regions=['VAL'])
    neurons_files =  mlapi.download_neurons(neurons_metadata[2:6]) 
    scene.add_neurons(neurons_files, soma_color='deepskyblue', force_to_hemisphere="right")

    scene.add_brain_regions(['VAL'], use_original_color=False, colors='palegreen', alpha=.9)
    mos = scene.actors['regions']['VAL']
    scene.edit_actors([mos], wireframe=True) 

    streamlines_files, data = streamlines_api.download_streamlines_for_region("VAL") 
    scene.add_streamlines(data[:1], color="palegreen", show_injection_site=False, alpha=.2, radius=10)

    set_camera(scene)
    scene.render()

# ---------------------------------------------------------------------------- #

def StreamlinesScene():
    streamlines_files, data = streamlines_api.download_streamlines_for_region("PAG") 

    scene = Scene()
    scene.add_streamlines(data[3], color="powderblue", show_injection_site=False, alpha=.3, radius=10)
    scene.add_brain_regions(['PAG'], use_original_color=False, colors='powderblue', alpha=.9)
    mos = scene.actors['regions']['PAG']
    scene.edit_actors([mos], wireframe=True) 

    set_camera(scene)
    scene.render() 

def StreamlinesScene2():
    scene = Scene()

    streamlines_files, data = streamlines_api.download_streamlines_for_region("VAL") 
    scene.add_streamlines(data, color="palegreen", show_injection_site=False, alpha=.3, radius=10)

    streamlines_files, data = streamlines_api.download_streamlines_for_region("VM") 
    scene.add_streamlines(data, color="palevioletred", show_injection_site=False, alpha=.3, radius=10)

    
    scene.add_brain_regions(['VAL'], use_original_color=False, colors='palegreen', alpha=.9, hemisphere='right')
    mos = scene.actors['regions']['VAL']
    scene.edit_actors([mos], wireframe=True) 

    scene.add_brain_regions(['VM'], use_original_color=False, colors='palevioletred', alpha=.9, hemisphere='right')
    mos = scene.actors['regions']['VM']
    scene.edit_actors([mos], wireframe=True) 

    set_camera(scene)
    scene.render() 

# ---------------------------------------------------------------------------- #

def ConnectivityScene():
    scene = Scene()
    p0 = scene.get_region_CenterOfMass("ZI")

    # Then we se these coordinates to get tractography data, note: any set of X,Y,Z coordinates would do. 
    tract = aba.get_projection_tracts_to_target(p0=p0)

    scene.add_tractography(tract, display_injection_structure=False, color_by="region", 
                        display_injection_volume=True, others_alpha=.25)
    scene.add_brain_regions(['ZI'], colors="ivory", alpha=1)

    set_camera(scene)
    scene.render()

# ---------------------------------------------------------------------------- #

def CellsScene():
    # Load and clean data
    data = pd.read_csv('/Users/federicoclaudi/Downloads/41593_2019_354_MOESM3_ESM.csv')
    data = data[['genotype', 'Xpos', 'Ypos', 'z.position']]
    data.columns = ['genotype', 'x', 'y', 'z']

    # Visualise data
    scene = Scene()
    scene.add_cells(data)

    set_camera(scene)
    scene.render() 







"""
    ================================================================================================================================
    ================================================================================================================================
"""


scenes = dict(
    BrainRegionsScene = BrainRegionsScene,
    NeuronsScene = NeuronsScene,
    StreamlinesScene = StreamlinesScene,
    StreamlinesScene2 = StreamlinesScene2,
    CellsScene = CellsScene,
    ConnectivityScene = ConnectivityScene,
    NeuronsScene2 = NeuronsScene2,
    NeuronsScene3 = NeuronsScene3,
)


if __name__ == "__main__":
    scene = "BrainRegionsScene"
    scenes[scene]()


