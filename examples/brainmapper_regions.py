"""
Visualise the output from brainmapper in some specific brain regions.
Cells transformed to atlas space can be found at
brainmapper_output/points/points.npy or exported by the brainmapper napari
widget

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

import numpy as np

settings.SHADER_STYLE = "plastic"
settings.SHOW_AXES = False

cells_path = Path(__file__).parent.parent / "resources" / "points.npy"

# Define regions of interest (easier to define all at the
# terminal/finest level of the hierarchy)
regions = ["VISp1", "VISp4", "VISp5"]

print(f"[{orange}]Running example: {Path(__file__).name}")


def get_cells_in_regions(scene, cells_path, regions):
    cells = np.load(cells_path)
    new_cells = []

    for cell in cells:
        if (
            scene.atlas.structure_from_coords(
                cell, as_acronym=True, microns=True
            )
            in regions
        ):
            if cell[0] > 0:
                new_cells.append(cell)

    new_cells = np.asarray(new_cells)

    return new_cells


# Create a brainrender scene
scene = Scene(title=f"brainmapper cells in {regions}", inset=False)

cells_points = get_cells_in_regions(scene, cells_path, regions)

# Create points actor
cells = Points(cells_points, radius=45, colors="palegoldenrod", alpha=0.8)

# Add specific regions
for region in regions:
    scene.add_brain_region(region, color="mediumseagreen", alpha=0.2)

# Add cells
scene.add(cells)

scene.render()
