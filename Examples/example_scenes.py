import sys
sys.path.append("./")
import pandas as pd

from brainrender import *
import brainrender
brainrender.SHADER_STYLE = 'cartoon'

from brainrender.scene import Scene
from brainrender.Utils.ABA.connectome import ABA

from brainrender.Utils.MouseLightAPI.mouselight_info import mouselight_api_info, mouselight_fetch_neurons_metadata
from brainrender.Utils.MouseLightAPI.mouselight_api import MouseLightAPI

from brainrender.Utils.parsers.streamlines import StreamlinesAPI
from brainrender.Utils.data_io import listdir
from brainrender.colors import get_n_shades_of


aba = ABA()
streamlines_api = StreamlinesAPI()
mlapi = MouseLightAPI()

# ---------------------------------------------------------------------------- #
#                   DEFINE A FUNCTION FOR EACH EXAMPLE SCENE                   #
# ---------------------------------------------------------------------------- #

def BrainRegionsScene():
    scene = Scene()
    scene.add_brain_regions(['TH', 'VP'], use_original_color=True, alpha=1)

    act = scene.actors['regions']['TH']
    scene.edit_actors([act], wireframe=True) 

    scene.render()

def CartoonStyleScene():
    if brainrender.SHADER_STYLE != 'cartoon':
        raise ValueError('Set cartoon style at imports')

    scene = Scene(camera='coronal', add_root=False)
    scene.add_brain_regions(['PAG', 'SCm', 'SCs'], use_original_color=True, alpha=1)
    # scene.add_brain_regions(['VISl', 'VISpl', 'VISpm', 'VISam', 'VISal', 'VISa'], use_original_color=True, alpha=.4)

    scene.render()


# ---------------------------------------------------------------------------- #

def NeuronsScene(show_regions = False):
    scene = Scene()

    fl = 'Examples/example_files/one_neuron.json'
    scene.add_neurons(fl, soma_color='darkseagreen', force_to_hemisphere="right",)

    if show_regions:
        scene.add_brain_regions(['ZI', 'PAG', 'MRN', 'NPC', "VTA", "STN", "PPT", "SCm", "HY"], 
                        use_original_color=True, alpha=.5)

    scene.render() 

# ---------------------------------------------------------------------------- #

def NeuronsScene2():
    scene = Scene()

    neurons_metadata = mouselight_fetch_neurons_metadata(filterby='soma', filter_regions=['MOp5'])
    neurons_files =  mlapi.download_neurons(neurons_metadata[2:6]) 
    scene.add_neurons(neurons_files, soma_color='deepskyblue', force_to_hemisphere="right")

    streamlines_files, data = streamlines_api.download_streamlines_for_region("MOp") 
    scene.add_streamlines(data[:1], color="palegreen", show_injection_site=False, alpha=.2, radius=10)

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

    scene.render()

# ---------------------------------------------------------------------------- #

def StreamlinesScene():
    streamlines_files, data = streamlines_api.download_streamlines_for_region("PAG") 

    scene = Scene()
    scene.add_streamlines(data[3], color="powderblue", show_injection_site=False, alpha=.3, radius=10)
    scene.add_brain_regions(['PAG'], use_original_color=False, colors='powderblue', alpha=.9)
    mos = scene.actors['regions']['PAG']
    scene.edit_actors([mos], wireframe=True) 

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

    scene.render()


# ---------------------------------------------------------------------------- #
def ElectrodesArrayScene():
    scene = Scene(add_root=False, camera='sagittal')
    z_offset = -1500
    scene.add_brain_regions(['VAL'], use_original_color=True, alpha=.5)
    scene.add_brain_regions(['TH'], use_original_color=True, alpha=.5, wireframe=True)

    # scene.add_optic_cannula('VAL')

    # for x_offset in [-200, -500, -800, -1100]:
    #     scene.add_optic_cannula('VAL', z_offset=z_offset, x_offset=x_offset, alpha=1,
    #                 radius=50, y_offset=-500, color='blackboard')

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
    ConnectivityScene = ConnectivityScene,
    NeuronsScene2 = NeuronsScene2,
    NeuronsScene3 = NeuronsScene3,
    CartoonStyleScene=CartoonStyleScene,
    ElectrodesArrayScene=ElectrodesArrayScene,
)


if __name__ == "__main__":
    scene = "ElectrodesArrayScene"
    scenes[scene]()



