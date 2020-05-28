"""
    This example shows how to create a scene that has a cartoony look 
    (good for schematics and illustrations)
"""

import brainrender

brainrender.SHADER_STYLE = "cartoon"  # gives actors a flat shading
from brainrender.scene import Scene

scene = Scene()

root = scene.actors["root"]
th = scene.add_brain_regions("TH", alpha=0.5)

# Create a black line around each actor
sil = root.silhouette().lw(1).c("k")
sil2 = th.silhouette().lw(3).c("k")

scene.add_vtkactor(sil, sil2)  # add the silhouette meshses to scene
scene.render()
