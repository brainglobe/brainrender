"""
    This tutorial shows 
            1) how to download and render neurons from the MouseLight project
                    using morphapi.
            2) how to these neurons with a few different options to color them

    You can also download data manually from the neuronbrowser website and render them by
    passing the downloaded files to `scene.add_neurons`.
"""
from brainrender.scene import Scene

from morphapi.api.mouselight import MouseLightAPI


# ---------------------------- Downloading neurons --------------------------- #
mlapi = MouseLightAPI()

# Fetch metadata for neurons with some in the secondary motor cortex
neurons_metadata = mlapi.fetch_neurons_metadata(
    filterby="soma", filter_regions=["MOs"]
)

# Then we can download the files and save them as a .json file
neurons = mlapi.download_neurons(neurons_metadata[:5])


# ----------------------------- Rendering neurons ---------------------------- #

# 1 color all neurons of the same color, don't show axons
scene = Scene(title="One color")
scene.add_neurons(
    neurons, color="salmon", display_axon=False, neurite_radius=6
)
scene.render()
scene.close()

# 2 color each neuron of a different color using a colormap
scene = Scene(title="Colormap")
scene.add_neurons(neurons, color="Reds", alpha=0.8)
scene.render()
scene.close()

# 3 specify a color for each neuron
scene = Scene(title="Color each")
scene.add_neurons(
    neurons,
    color=["salmon", "darkseagreeb", "skyblue", "chocolate", "darkgoldenrod"],
    alpha=0.8,
)
scene.render()
scene.close()

# 4 specify a color for each neuronal component
scene = Scene(title="Color components")
scene.add_neurons(
    neurons, color=dict(soma="red", dendrites="orange", axon="blackboard")
)
scene.render()
scene.close()


""" 
    For more options check the add_neurons function docstring (atlases.aba.Aba -> add_neurons).
    Also check 'colored_neurons.py' example for using a custom colormap.
"""
