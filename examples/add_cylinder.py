"""
    This example shows how to add a cylinder actor to a scene (e.g. 
    to represent the location of an implanted optic canula)
"""
from brainrender import Scene
from brainrender import settings

from brainrender.actors import Cylinder

settings.SHOW_AXES = False
settings.WHOLE_SCREEN = False


from rich import print
from myterial import orange
from pathlib import Path

print(f"[{orange}]Running example: {Path(__file__).name}")

scene = Scene(inset=False, title="optic canula")

th = scene.add_brain_region(
    "TH",
    alpha=0.4,
)

# create and add a cylinder actor
actor = Cylinder(
    th,  # center the cylinder at the center of mass of th
    scene.root,  # the cylinder actor needs information about the root mesh
)

scene.add(actor)
scene.render(zoom=1.6)
