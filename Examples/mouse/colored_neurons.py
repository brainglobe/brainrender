"""
    This example shows how download neurons from the 
    mouselight datase with morphapi and render 
    them with a custom colors palette
"""

import brainrender

brainrender.SHADER_STYLE = "cartoon"
brainrender.ROOT_ALPHA = 0.3
brainrender.BACKGROUND_COLOR = "blackboard"


from brainrender.scene import Scene
from brainrender.colors import makePalette

from morphapi.api.mouselight import MouseLightAPI


# ---------------------------- Downloading neurons --------------------------- #
mlapi = MouseLightAPI()

# Fetch metadata for neurons with some in the secondary motor cortex
neurons_metadata = mlapi.fetch_neurons_metadata(
    filterby="soma", filter_regions=["MOs"]
)

# Then we can download the files and save them as a .json file
neurons = mlapi.download_neurons(
    neurons_metadata[:50]
)  # 50 neurons, might take a while the first time


# ----------------------------- Rendering neurons ---------------------------- #

# Create a custom colormap between 3 colors
colors = makePalette(len(neurons), "salmon", "lightgreen")

# Create scene
scene = Scene(add_root=True, display_inset=False, title="neurons")

# Add each neuron with it's color
scene.add_neurons(neurons, alpha=0.8, neurite_radius=8, color=colors)

# Cut all actors to expose neurons
scene.cut_actors_with_plane("sagittal")
scene.render()
