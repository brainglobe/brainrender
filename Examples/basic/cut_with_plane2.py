"""
    This example shows how to cut selected actors in the scene using a 
    custom plane 
"""

import brainrender
brainrender.SHADER_STYLE = 'cartoon'

from brainrender.scene import Scene
import numpy as np
from vtkplotter import Plane

scene = Scene(use_default_key_bindings=True)

# Add some actors
root = scene.actors['root']
th = scene.add_brain_regions(['STR', 'TH'], alpha=.5)

# Specify position, size and orientation of the plane
pos = scene.atlas._root_midpoint
sx, sy = 15000, 15000
norm = [0, 1, 1]
plane = scene.atlas.get_plane_at_point(pos, norm, sx, sy, color='lightblue')

# Cut
scene.cut_actors_with_plane(plane, close_actors=False, # set close_actors to True close the holes left by cutting
                showplane=True, actors=scene.actors['root'])

sil = root.silhouette().lw(1).c('k')
scene.add_vtkactor(sil)

scene.render(camera='top')