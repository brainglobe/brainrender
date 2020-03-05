"""
    This tutorial shows how to use the AllenMorphology to download neuron morphology data
    from the Allen Cell types database and render them in brainrender. 

    The same AllenMorphology class can be used to render any '*.swc' file. 
"""
import brainrender
brainrender.SHADER_STYLE = 'cartoon'
from brainrender.Utils.AllenMorphologyAPI.AllenMorphology import AllenMorphology

am = AllenMorphology(scene_kwargs={'title':'A single neuron.'})

print(am.neurons.head()) # this dataframe has metadata for all available neurons

neurons = am.download_neurons(am.neurons.id.values[0]) # download one neruons

# Render 
am.add_neuron(neurons, color='salmon')
am.render(zoom=1)
