from brainrender import Scene
from brainrender.actors.streamlines import (
    make_streamlines,
    get_streamlines_for_region,
)

# Create a brainrender scene
scene = Scene()

# Add brain regions
scene.add_brain_region("TH")

# Get stramlines data and add
streams = get_streamlines_for_region("TH")
scene.add(*make_streamlines(*streams, color="salmon", alpha=0.5))

# Render!
scene.render()
