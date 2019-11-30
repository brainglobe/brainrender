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
from BrainRender.colors import get_n_shades_of

aba = ABA()
streamlines_api = StreamlinesAPI()


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


# DEFINE A FUNCTION FOR EACH EXAMPLE SCENE, THEN CALL THE ONE YOU WANT TO DISPLAY_ROOT
def BrainRegionsScene():
    scene = Scene()
    scene.add_brain_regions(['TH', 'VP'], use_original_color=True, alpha=1)

    act = scene.actors['regions']['TH']
    scene.edit_actors([act], wireframe=True) 

    set_camera(scene)
    scene.render()


def NeuronsScene(show_regions = False):
    scene = Scene()

    fl = 'Examples/example_files/one_neuron.json'
    scene.add_neurons(fl, soma_color='darkseagreen', force_to_hemisphere="right",)

    if show_regions:
        scene.add_brain_regions(['ZI', 'PAG', 'MRN', 'NPC', "VTA", "STN", "PPT", "SCm", "HY"], 
                        use_original_color=True, alpha=.5)


    set_camera(scene)
    scene.render() 


def StreamlinesScene():
    streamlines_files, data = streamlines_api.download_streamlines_for_region("PAG") 

    scene = Scene()
    scene.add_streamlines(data[3], color="powderblue", show_injection_site=False, alpha=.75, radius=10)
    scene.add_brain_regions(['PAG'], use_original_color=False, colors='powderblue', alpha=.9)
    mos = scene.actors['regions']['PAG']
    scene.edit_actors([mos], wireframe=True) 

    set_camera(scene)
    scene.render() 

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
    CellsScene = CellsScene,
    ConnectivityScene = ConnectivityScene,
)


if __name__ == "__main__":
    scene = "NeuronsScene"
    scenes[scene]()


