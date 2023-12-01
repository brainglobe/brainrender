from pathlib import Path

from myterial import orange
from rich import print

from brainrender import Scene

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a brainrender scene using the zebrafish atlas
scene = Scene(atlas_name="mpin_zfish_1um", title="zebrafish")

# Render!
scene.render()
