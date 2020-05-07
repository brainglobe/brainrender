"""
    This example shows how to render 50 neurons
    from the mouselight database coloring each with
    a color from an user-defined colormap
"""

import brainrender
brainrender.SHADER_STYLE = 'cartoon'
brainrender.ROOT_ALPHA = 0.3
brainrender.ROOT_COLOR = 'ivory'


from brainrender.scene import Scene
from brainrender.colors import makePalette

from brainrender.Utils.MouseLightAPI.mouselight_api import MouseLightAPI
from brainrender.Utils.MouseLightAPI.mouselight_info import mouselight_api_info, mouselight_fetch_neurons_metadata



# Fetch metadata for neurons with some in the secondary motor cortex
neurons_metadata = mouselight_fetch_neurons_metadata(filterby='soma', filter_regions=['MOs'])

# Then we can download the files and save them as a .json file
ml_api = MouseLightAPI() 
neurons_files =  ml_api.download_neurons(neurons_metadata[:50]) # just saving the first couple neurons to speed things up

# Create colormap
colors1 = makePalette('salmon', 'lightgreen', int(len(neurons_files)/2+1))
colors2 = makePalette('lightgreen', 'lightblue', int(len(neurons_files)/2+1))
colors = colors1 + colors2

# Create scene
scene = Scene(add_root=True, display_inset=False)

# Add each neuron with it's color
for color, neuron in zip(colors, neurons_files):
    scene.add_neurons(neuron, soma_color=color, alpha=.8, neurite_radius=8) # add_neurons takes a lot of arguments to specify how the neurons should look

# Cut scene to expose neurons
scene.cut_actors_with_plane('sagittal')
scene.render() 