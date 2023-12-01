from pathlib import Path
from importlib.resources import files

from myterial import orange
from rich import print

from brainrender import Scene

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a brainrender scene
scene = Scene(title="Injection in SCm")

# Add brain SCm
scene.add_brain_region("SCm", alpha=0.2)

# Add from file
scene.add(
    files("brainrender").joinpath("resources/CC_134_1_ch1inj.obj"),
    color="tomato",
)

# Render!
scene.render()
