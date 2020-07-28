"""
    This example shows how to create a scene that has a cartoony look 
    (good for schematics and illustrations)
"""

import brainrender

brainrender.SHADER_STYLE = "cartoon"  # gives actors a flat shading
from brainrender.scene import Scene

scene = Scene(title="cartoon look")
th = scene.add_brain_regions("TH", alpha=0.5)

# Create a black line around each actor
scene.add_silhouette(scene.root)
scene.add_silhouette(th, lw=3)

scene.render()
