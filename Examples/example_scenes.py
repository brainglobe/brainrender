import sys
sys.path.append("./")
import pandas as pd

from BrainRender.scene import Scene
from BrainRender.variables import *
from BrainRender.Utils.ABA.connectome import ABA

from BrainRender.Utils.MouseLightAPI.mouselight_info import mouselight_api_info, mouselight_fetch_neurons_metadata
from BrainRender.Utils.MouseLightAPI.mouselight_download_neurons import download_neurons

from BrainRender.Utils.parsers.streamlines import StreamlinesAPI
from BrainRender.Utils.data_io import listdir

aba = ABA()
streamlines_api = StreamlinesAPI()

# DEFINE A FUNCTION FOR EACH EXAMPLE SCENE, THEN CALL THE ONE YOU WANT TO DISPLAY_ROOT
def BrainRegionsScene():
    scene = Scene()
    scene.add_brain_regions(['CA2', 'CA3'], use_original_color=False, colors="ivory", alpha=1)
    scene.add_brain_regions(['CA1'], use_original_color=True, alpha=1)

    scene.render()


def NeuronsScene():
    neurons_metadata = mouselight_fetch_neurons_metadata(filterby='soma', filter_regions=['MOs6b'])
    neurons_files =  download_neurons(neurons_metadata)

    scene = Scene()
    scene.add_neurons(neurons_files, soma_color="darkseagreen", force_to_hemisphere="right")
    scene.add_brain_regions(['MOs'], use_original_color=True, alpha=.4)
    mos = scene.actors['regions']['MOs']
    scene.edit_actors([mos], wireframe=True) 
    scene.render() 


def StreamlinesScene():
    streamlines_files, data = streamlines_api.download_streamlines_for_region("MOs") 

    scene = Scene()
    scene.add_streamlines(data[:2], color="darkseagreen", show_injection_site=False, alpha=.75, radius=10)
    scene.add_brain_regions(['MOs'], use_original_color=True, alpha=.9)
    mos = scene.actors['regions']['MOs']
    scene.edit_actors([mos], wireframe=True) 
    scene.render() 

def ConnectivityScene():
    scene = Scene()
    p0 = scene.get_region_CenterOfMass("ZI")

    # Then we se these coordinates to get tractography data, note: any set of X,Y,Z coordinates would do. 
    tract = aba.get_projection_tracts_to_target(p0=p0)
    # scene.add_tractography(tract, display_injection_structure=False, color_by="target_region", display_injection_volume=False,
    #                     VIP_regions=['MOs'], VIP_color="darkseagreen", others_color="ivory", others_alpha=.25)
    scene.add_tractography(tract, display_injection_structure=False, color_by="region", 
                        display_injection_volume=False, others_alpha=.25)
    scene.add_brain_regions(['ZI'], colors="darkred", alpha=1)
    scene.render()


def CellsScene():
    # Load and clean data
    data = pd.read_csv('/Users/federicoclaudi/Downloads/41593_2019_354_MOESM3_ESM.csv')
    data = data[['genotype', 'Xpos', 'Ypos', 'z.position']]
    data.columns = ['genotype', 'x', 'y', 'z']

    # Visualise data
    scene = Scene()
    scene.add_cells(data)
    scene.render() 







"""
    ================================================================================================================================
    ================================================================================================================================
"""


scenes = dict(
    BrainRegionsScene = BrainRegionsScene,
    NeuronsScene = NeuronsScene,
    StreamlinesScene = StreamlinesScene,
    CellsScene = CellsScene,
    ConnectivityScene = ConnectivityScene,
)


if __name__ == "__main__":
    scene = "ConnectivityScene"
    scenes[scene]()
