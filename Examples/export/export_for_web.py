"""
    This example shows how a brainrender scene can be exorted to a .html file.
    You can then open the html file in a browser to render an interactive brainrender scene
"""

import brainrender

brainrender.SHADER_STYLE = "cartoon"
from brainrender.scene import Scene

# Create a scene
scene = Scene()

# Add the whole thalamus in gray
scene.add_brain_regions(["TH"], alpha=0.15)


scene.export_for_web()  # <- you can pass a  filepath to specify where to save the scene
