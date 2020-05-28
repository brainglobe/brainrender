"""
    This example shows how to cut actors in the scene using a plane
    oriented along the sagittal axis
"""

import brainrender

brainrender.SHADER_STYLE = "cartoon"

from brainrender.scene import Scene


scene = Scene()

# Add some actors
root = scene.actors["root"]
th = scene.add_brain_regions(["STR", "TH"], alpha=0.5)

# Cut with plane
scene.cut_actors_with_plane(
    "sagittal", showplane=False
)  # Set showplane to True if you want to see the plane location

# Add a silhouette around each actor to emphasize the cut location
sil = root.silhouette().lw(1).c("k")
sil2 = [act.silhouette().lw(3).c("k") for act in th]
scene.add_vtkactor(sil, *sil2)

scene.render(camera="top")
