from brainrender import Scene

from rich import print
from myterial import orange
from pathlib import Path

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a brainrender scene
scene = Scene(title="brain regions")

# Add brain regions
scene.add_brain_region("TH")

# You can specify color, transparency...
scene.add_brain_region("MOs", "CA1", alpha=0.2, color="green")

# Render!
scene.render()
