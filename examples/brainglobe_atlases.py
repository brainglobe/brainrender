from brainrender import Scene

from rich import print
from myterial import orange
from pathlib import Path

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a brainrender scene using the zebrafish atlas
scene = Scene(atlas_name="mpin_zfish_1um", title="zebrafish")

# Render!
scene.render()
