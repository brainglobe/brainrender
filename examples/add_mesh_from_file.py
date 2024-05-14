from pathlib import Path

from myterial import orange
from rich import print

from brainrender import Scene

obj_file = resources_dir = (
    Path(__file__).parent.parent / "resources" / "CC_134_1_ch1inj.obj"
)

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a brainrender scene
scene = Scene(title="Injection in SCm")

# Add brain SCm
scene.add_brain_region("SCm", alpha=0.2)

# Add from file
scene.add(obj_file, color="tomato")

# Render!
scene.render()
