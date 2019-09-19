# %%
import sys
sys.path.append('./') 
from anatomy.brain_render import BrainRender
import os
analyzer = BrainRender()
from vtkplotter import *
import pandas as pd
#%%
sets = analyzer.other_sets
sets_names = sorted(list(sets.keys()))

#%%
hypothalamus_structures = list(sets["Summary structures of the hypothalamus"].acronym.values)
thalamus_structures = list(sets["Summary structures of the thalamus"].acronym.values)
pons_structures = list(sets["Summary structures of the pons"].acronym.values)
midbrain_structures = list(sets["Summary structures of the midbrain"].acronym.values)

neurons_fld = "D:\\Dropbox (UCL - SWC)\\Rotation_vte\\analysis_metadata\\anatomy\\Mouse Light"
neurons_file = os.path.join(neurons_fld, "one_neuron.json")

# %%
tract = analyzer.get_projection_tracts_to_target("PAG")

# %%
vp = analyzer.plot_structures_3d(["PAG", "SCm"], render=False, others_alpha=.5)
# vp = analyzer.render_injection_sites(experiments, render=False, vp=vp)
vp = analyzer.render_tractography(tract, render=True, vp=vp)
# ! TODO write function to get 3d MESH points, centroid etc...

