"""
    This tutorial shows how to download and render neurons from the MouseLight project
    using the MouseLightAPI class. 

    You can also download data manually from the neuronbrowser website and render them by
    passing the downloaded files to `scene.add_neurons`.
"""
import brainrender
brainrender.USE_MORPHOLOGY_CACHE = True
from brainrender.scene import Scene
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
scene.render(camera='coronal') 