from pathlib import Path

from myterial import orange
from rich import print

from brainrender import Scene
from brainrender.actors.streamlines import make_streamlines
from brainrender.atlas_specific import get_streamlines_for_region

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
