"""
    This example shows how to add a label to a renderend actor
"""

from brainrender import Scene

from rich import print
from myterial import orange
from pathlib import Path

print(f"[{orange}]Running example: {Path(__file__).name}")

# crate a scene and add brain regions
scene = Scene()
th, mos = scene.add_brain_region("TH", "MOs")
scene.add_label(th, "TH")
scene.add_label(mos, "My region")

# render
scene.render()
