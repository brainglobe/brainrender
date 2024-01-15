from pathlib import Path

from myterial import orange
from rich import print

from brainrender import Scene

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a brainrender scene
scene = Scene(title="brainrender web export")

# Add brain regions
scene.add_brain_region("MOs", "CA1", alpha=0.2, color="green", hemisphere="right")

# Render!
scene.render()

# Export to web
scene.export("brain_regions.html")
