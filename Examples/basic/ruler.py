"""
    This example shows how to measure and display
    the distance between two points.
"""

from brainrender.scene import Scene
import brainrender
from vedo import Ruler

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
    the unitScale argument.
"""
rul = Ruler(
    p2,
    p1,  # Vedo Ruler
    unitScale=0.01,
    units="mm",
    precision=4,
    s=200,
    axisRotation=0,
    tickAngle=70,
)
scene.add_actor(rul)

# render
scene.render()
