"""
    This example shows how to cut actors in the scene using a plane
    oriented along the sagittal axis
"""

import brainrender

brainrender.SHADER_STYLE = "cartoon"

from brainrender.scene import Scene


scene = Scene(title="cut with plane")

# Add some actors
th = scene.add_brain_regions(["STR", "TH"], alpha=0.5)

# Cut with plane
scene.cut_actors_with_plane(
    "sagittal", showplane=False
)  # Set showplane to True if you want to see the plane location

# Add a silhouette around each actor to emphasize the cut location
scene.add_silhouette(*th, lw=3)


scene.render(camera="top")
