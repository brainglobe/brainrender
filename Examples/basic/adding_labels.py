"""
    This tutorial shows how to use flags (strings of text that appear when you mose hoover over an actor)
    to add more information about the actors in your rendering. 
"""


import brainrender
brainrender.SHADER_STYLE = 'cartoon'
from brainrender.scene import Scene

# Create a scene
scene = Scene()

scene.add_brain_regions(['VAL'], use_original_color=True, add_labels=True)

scene.render()