# %%
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from allensdk.core.cell_types_cache import CellTypesCache
from allensdk.core.cell_types_cache import CellTypesCache
from allensdk.api.queries.cell_types_api import CellTypesApi
from allensdk.core.cell_types_cache import ReporterStatus as RS
from allensdk.core.swc import Marker


# %matplotlib inline
# %%
cells_flds = "D:\\Dropbox (UCL - SWC)\\Rotation_vte\\analysis_metadata\\anatomy\\Cell Types"

ctc = CellTypesCache(manifest_file=os.path.join(cells_flds, "manifest.json"))
# mouse cells
mouse_cells = ctc.get_cells(species=[CellTypesApi.MOUSE])
print("Mouse cells: %d" % len(mouse_cells))

# cells with reconstructions and no Cre
cells_with_reconstruction = ctc.get_cells(species=[CellTypesApi.MOUSE], require_reconstruction = True, reporter_status = RS.NEGATIVE)
print("Cells with reconstructions: %d" % len(cells_with_reconstruction))



#%%
# download and open an SWC file
cell_id = 480114344
morphology = ctc.get_reconstruction(cell_id) 
markers = ctc.get_reconstruction_markers(cell_id) 

#%%
fig, axes = plt.subplots(1, 2, sharey=True, sharex=True)
axes[0].set_aspect('equal', 'box-forced')
axes[1].set_aspect('equal', 'box-forced')

# Make a line drawing of x-y and y-z views
for n in morphology.compartment_list:
    for c in morphology.children_of(n):
        axes[0].plot([n['x'], c['x']], [n['y'], c['y']], color='black')
        axes[1].plot([n['z'], c['z']], [n['y'], c['y']], color='black')

# cut dendrite markers
dm = [ m for m in markers if m['name'] == Marker.CUT_DENDRITE ]

axes[0].scatter([m['x'] for m in dm], [m['y'] for m in dm], color='#3333ff')
axes[1].scatter([m['z'] for m in dm], [m['y'] for m in dm], color='#3333ff')

# no reconstruction markers
nm = [ m for m in markers if m['name'] == Marker.NO_RECONSTRUCTION ]

axes[0].scatter([m['x'] for m in nm], [m['y'] for m in nm], color='#333333')
axes[1].scatter([m['z'] for m in nm], [m['y'] for m in nm], color='#333333')

axes[0].set_ylabel('y')
axes[0].set_xlabel('x')
axes[1].set_xlabel('z')


#%%
