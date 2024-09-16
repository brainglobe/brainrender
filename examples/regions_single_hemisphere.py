"""
Example to visualise brain regions in a single hemisphere
"""

from pathlib import Path

from myterial import orange
from rich import print

from brainrender import Scene

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a brainrender scene
scene = Scene(title="Left hemisphere", atlas_name="allen_mouse_25um")

# Add brain regions
scene.add_brain_region("CP", "VISp", hemisphere="left")

# Render!
scene.render()
