"""
    This example shows how to cut selected actors in the scene using a 
    custom plane 
"""

import brainrender

brainrender.SHADER_STYLE = "cartoon"
from brainrender.scene import Scene


scene = Scene(use_default_key_bindings=True, title="cut with plane")

# Add some actors
th = scene.add_brain_regions(["STR", "TH"], alpha=0.5)

# Specify position, size and orientation of the plane
pos = scene.atlas._root_midpoint
sx, sy = 15000, 15000
norm = [0, 1, 1]
plane = scene.atlas.get_plane_at_point(
    pos, norm=norm, sx=sx, sy=sy, color="lightblue"
)

# Cut
scene.cut_actors_with_plane(
    plane,
    close_actors=False,  # set close_actors to True close the holes left by cutting
    showplane=True,
    actors=scene.root,
)

sil = scene.root.silhouette().lw(1).c("k")
scene.add_actor(sil)

scene.render(camera="top")
