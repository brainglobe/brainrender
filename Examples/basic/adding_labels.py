"""
    This tutorial shows how to use flags (strings of text that appear when you mose hoover over an actor)
    to add more information about the actors in your rendering. 
"""


import brainrender

brainrender.SHADER_STYLE = "cartoon"
from brainrender.scene import Scene

# Create a scene
scene = Scene(title="labels")

# add_brain_regions can be used to add labels directly
scene.add_brain_regions("VAL", add_labels=True)

# you can also use scene.add_actor_label
mos = scene.add_brain_regions("MOs")

# Add another label, this time make it gray and shift it slightly
scene.add_actor_label(mos, "MOs", size=400, color="blackboard", xoffset=250)

scene.render()
