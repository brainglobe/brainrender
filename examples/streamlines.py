from brainrender import Scene
from brainrender.atlas_specific import get_streamlines_for_region
from brainrender.actors.streamlines import make_streamlines

from rich import print
from myterial import orange
from pathlib import Path

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a brainrender scene
scene = Scene()

# Add brain regions
scene.add_brain_region("TH")

# Get stramlines data and add
streams = get_streamlines_for_region("TH")[:2]
scene.add(*make_streamlines(*streams, color="salmon", alpha=0.5))

# Render!
scene.render()
