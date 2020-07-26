import brainrender

brainrender.SHADER_STYLE = "cartoon"


from brainrender.scene import Scene
from brainrender.atlases.custom_atlaseselegans import Celegans

# Specify path to folder with c.elegans connectome

"""
        Currently Celegans assumes that you already possess the data.
        If this is not the case, please do get in touch. 
        We will be adding support to automatically download these data soon!
"""

data_folder = "/Users/federicoclaudi/Dropbox (UCL - SWC)/Rotation_vte/Anatomy/Atlases/atlasesforbrainrender/CELEGANS"


# --------------------------- Scene 1: all neurons --------------------------- #

# Create a brainrender scene with a custom Atlas class
"""
    By passing a custom Atlas class (instance of brainrender.atlases.base Atlas class)
    to Scene, Scene will use the atlas class' methods to fetch data and crate actors.
"""
scene = Scene(
    add_root=False,
    atlas=Celegans,  # Pass the custom atlas class to scene.
    display_inset=False,
    atlas_kwargs=dict(
        data_folder=data_folder
    ),  # use this to pass keyword arguments to the Atlas class
    title="Whole connectome",
)


# Exclude some neurons we don't want to render
metadata = scene.atlas.neurons_metadata
neurons = metadata.loc[
    (metadata.type != "nonvalid") & (metadata.type != "other")
]


# Add each neuron with the corresponding outline
scene.add_neurons(list(neurons.neuron.values))
for neuron in scene.actors["neurons"]:
    scene.add_actor(neuron.silhouette().lw(3).c("k"))

# Render
scene.render()
scene.close()

# ------------------------- Scene 2: showing synapses ------------------------ #


scene = Scene(
    add_root=False,
    atlas=Celegans,  # Pass the custom atlas class to scene.
    display_inset=False,
    atlas_kwargs=dict(
        data_folder=data_folder
    ),  # use this to pass keyword arguments to the Atlas class
    title="Synapses",
)

# Show only a few neurons and their pre and post synapses
scene.add_neurons(
    list(neurons.neuron.values[:5]), as_skeleton=True
)  # You can render the neruons as just their skeleton

scene.add_neurons_synapses(
    list(neurons.neuron.values[:5]), pre=True, post=True
)
"""
        Pre-synaptic locations are shown as grey spheres, 
        post-synaptic ones as arrows point towards the post-synaptic target.
"""

scene.render()
