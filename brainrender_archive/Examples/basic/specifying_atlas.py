"""
    This example shows you two way to specify at atlas other than the default one. 
"""
import brainrender
from brainrender.scene import Scene

scene = Scene(atlas="allen_human_500um", title="human atlas")
scene.render()
scene.close()

# Second method: modify default atlas
brainrender.DEFAULT_ATLAS = "allen_human_500um"
scene = Scene(title="human atlas")
scene.render()
