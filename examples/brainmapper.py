"""
Visualise the output from brainmapper.
Cells transformed to atlas space can be found at
brainmapper_output/points/points.npy or exported by the brainmapper
napari widget

For more details on brainmapper, please see:
- https://brainglobe.info/documentation/brainglobe-workflows/brainmapper/index.html
- https://brainglobe.info/documentation/brainglobe-utils/transform-widget.html
"""

from pathlib import Path

from myterial import orange
from rich import print

from brainrender.scene import Scene
from brainrender.actors import Points
from brainrender import settings

settings.SHADER_STYLE = "plastic"

cells_path = Path(__file__).parent.parent / "resources" / "points.npy"

print(f"[{orange}]Running example: {Path(__file__).name}")

# Create a brainrender scene
scene = Scene(title="brainmapper cells")

# Create points actor
cells = Points(cells_path, radius=45, colors="palegoldenrod", alpha=0.8)

# Visualise injection site
scene.add_brain_region("VISp", color="mediumseagreen", alpha=0.6)

# Add cells
scene.add(cells)

scene.render()
