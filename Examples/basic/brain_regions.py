""" 
    This tutorial shows how to create and render a brainrender scene with some brain regions
"""
import brainrender

brainrender.SHADER_STYLE = "cartoon"
from brainrender.scene import Scene

# Create a scene
scene = Scene(title="brain regions")

# Add the whole thalamus in gray
scene.add_brain_regions(["TH"], alpha=0.15)

# Add VAL nucleus in wireframe style with the allen color
val = scene.add_brain_regions(["VAL"], use_original_color=True)
val.wireframe()

scene.render()
