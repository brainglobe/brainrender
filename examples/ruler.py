from brainrender import Scene
from brainrender.actors import ruler, ruler_from_surface

from rich import print
from myterial import orange
from pathlib import Path

print(f"[{orange}]Running example: {Path(__file__).name}")

scene = Scene(title="rulers")

th, mos = scene.add_brain_region("TH", "MOs", alpha=0.3)

# Get a ruler between the two regions
p1 = th.centerOfMass()
p2 = mos.centerOfMass()

rul1 = ruler(p1, p2, unit_scale=0.01, units="mm")

# Get a ruler between thalamus and brian surface
rul2 = ruler_from_surface(p1, scene.root, unit_scale=0.01, units="mm")

scene.add(rul1, rul2)
scene.render()
