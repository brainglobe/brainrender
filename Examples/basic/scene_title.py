""" 
    This tutorial shows how to create and render a brainrender scene with a title on top
"""
import brainrender

brainrender.SHADER_STYLE = "cartoon"
from brainrender.scene import Scene

scene = Scene(title="The thalamus.")

# You can use scene.add_text to add other text elsewhere in the scene.

scene.add_brain_regions(["TH"], alpha=0.4)
scene.render(camera="sagittal")
