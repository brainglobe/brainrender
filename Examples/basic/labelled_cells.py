""" 
    This tutorial shows how to show the position of labelled cells in brainrender
"""
import pandas as pd

import brainrender

brainrender.SHADER_STYLE = "cartoon"
from brainrender.scene import Scene
from brainrender.Utils.scene_utils import get_n_random_points_in_region

# Create a scene
scene = Scene(
    title="labelled cells"
)  # specify that you want a view from the top


# Gerate the coordinates of N cells across 3 regions
regions = ["MOs", "VISp", "ZI"]
N = 1000  # getting 1k cells per region, but brainrender can deal with >1M cells easily.

# Render regions
scene.add_brain_regions(regions, alpha=0.2)

# Get fake cell coordinates
cells = []  # to store x,y,z coordinates
for region in regions:
    region_cells = get_n_random_points_in_region(
        scene.atlas, region=region, N=N
    )
    cells.extend(region_cells)
x, y, z = [c[0] for c in cells], [c[1] for c in cells], [c[2] for c in cells]
cells = pd.DataFrame(
    dict(x=x, y=y, z=z)
)  # ! <- coordinates should be stored as a pandas dataframe


# Add cells
scene.add_cells(cells, color="darkseagreen", res=12, radius=25)

# render
scene.render()
