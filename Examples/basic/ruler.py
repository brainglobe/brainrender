"""
    This example shows how to measure and display
    the distance between two points.
"""


from brainrender.scene import Scene
import brainrender
from brainrender import ruler


brainrender.SHOW_AXES = True

# Create Scene
scene = Scene()

# add brain regions
mos, hy = scene.add_brain_regions(["MOs", "HY"], alpha=0.2)
mos.wireframe()
hy.wireframe()

# Get center of mass of the two regions
p1 = scene.atlas.get_region_CenterOfMass("MOs")
p2 = scene.atlas.get_region_CenterOfMass("HY")


# Use the ruler class to display the distance between the two points
"""
    Brainrender units are in micrometers. To display the distance
    measure instead we will divide by a factor of 1000 using 
    the unit_scale argument.
"""

# Add a ruler form the brain surface
scene.add_ruler_from_surface(p2)

# Add a ruler between the two regions
scene.add_actor(ruler(p1, p2, unit_scale=0.01, units="mm"))

# render
scene.render()
