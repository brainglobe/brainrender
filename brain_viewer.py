# %%
import sys
sys.path.append('./')   # <- necessary to import packages from other directories within the project
from Utilities.imports import *
get_ipython().magic('matplotlib inline')

from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache


# %%
class BrainViewer:
	main_structures = ["Periaqueductal gray", 
						'Superior colliculus, motor related',
						"Gigantocellular reticular nucleus",
						"Zona incerta"]


	def __init__(self):
		fld = "D:\\Dropbox (UCL - SWC)\\Rotation_vte\\analysis_metadata\\anatomy\\mouse_connectivity"
		manifest = os.path.join(fld, "manifest.json")
		self.mcc = MouseConnectivityCache(manifest_file=manifest)

		self.structure_tree = self.mcc.get_structure_tree()

		# acronym map
		acronym_map = self.structure_tree.value_map(lambda x: x['id'], lambda y: y['acronym'])

		# Get template
		# ? get brainz templates
		self.template, template_info = self.mcc.get_template_volume()
		self.annot, annot_info = self.mcc.get_annotation_volume()

		# Get reference space
		self.space =self.mcc.get_reference_space()


	################################################################################
			# DATA GETTERS
	##############################################################################

		
	def get_structure_wt_experiments(self, structures):
		experiments = self.mcc.get_experiments(cre=False,  injection_structure_ids=[self.structures_details[structure]['id']])
		experiments_ids = [ e['id'] for e in experiments ]

		return experiments, experiments_ids

	def get_structure_binary_mask(self, structure_id):
		# To see the id, use get_structures
		mask, info = self.mcc.get_structure_mask(structure_id)
		return mask, info


	################################################################################
			# DATA PLOTTERS
	################################################################################
	
	def view_template(self, slice_id = 100):
		f, axarr = create_figure(subplots=True, ncols=3)

		for i, ax in enumerate(axarr):
			ax.imshow(self.space.get_slice_image(i, 5000), interpolation='none', origin="upper")

	def view_experiment(self, exp):
		# Get max projection
		experiment_id = exp["id"]
		# projection density: number of projecting pixels / voxel volume
		proj, proj_info = bv.mcc.get_projection_density(experiment_id)

		f, axarr = create_figure(subplots=True, ncols=3, figsize=(16,16))

		slices = [exp["injection_x"], exp["injection_y"], exp["injection_z"]]

		for i, (ax, slice_idx) in enumerate(zip(axarr, slices)):
			ax.imshow(bv.space.get_slice_image(i, slice_idx), interpolation='none', origin="upper")

			max_proj = proj.max(axis=i)
			max_proj[max_proj <= np.nanmean(max_proj)*2] = np.nan
			ax.imshow(max_proj, cmap='hot', aspect='equal', origin="upper", alpha=.85)


	def view_multiple_experiments(self, experiments_ids, mask_structure=None):

		f, axarr = plt.subplots(ncols=3, nrows=10, figsize=(24, 24))

		n_slices = self.template.shape # x, y, z
		slices_idxs = [np.linspace(10, nsl-10, 10) for nsl in n_slices]

		if mask_structure is not None:
			mask, info = self.get_structure_binary_mask(self.structures_details[mask_structure]["id"])


		for i in range(10):
			x_slice, y_slice, z_slice = np.int(slices_idxs[0][i]), np.int(slices_idxs[1][i]), np.int(slices_idxs[2][i])
			axarr[i,0].imshow(self.template[x_slice, :, :], interpolation='none', origin="upper", aspect="equal")
			axarr[i,1].imshow(self.template[:, y_slice, :], interpolation='none', origin="upper", aspect="equal")
			axarr[i,2].imshow(np.rot90(self.template[:, :, z_slice], 3), interpolation='none', origin="upper", aspect="equal")

		for ax in axarr.flatten():
			ax.set(xticks=[], yticks=[])



	def view_multiple_brain_regions(self, regions_acronyms, cmaps):
		if len(regions_acronyms) != len(cmaps): raise ValueError("give me regions give me colors plis")

		f, axarr = plt.subplots(ncols=3, nrows=10, figsize=(24, 24))

		n_slices = self.template.shape # x, y, z
		slices_idxs = [np.linspace(50, nsl-50, 10) for nsl in n_slices]

		masks = []
		for region in regions_acronyms:
			region_id = self.structures_details[region]["id"]
			mask, info = self.get_structure_binary_mask(region_id)
			mask = mask.astype(np.float)
			mask[mask == 0] = np.nan
			masks.append(mask)

		for i in range(10):
			x_slice, y_slice, z_slice = np.int(slices_idxs[0][i]), np.int(slices_idxs[1][i]), np.int(slices_idxs[2][i])
			axarr[i,0].imshow(self.template[x_slice, :, :], interpolation='none', origin="upper", aspect="equal")
			axarr[i,1].imshow(self.template[:, y_slice, :], interpolation='none', origin="upper", aspect="equal")
			axarr[i,2].imshow(np.rot90(self.template[:, :, z_slice], 3), interpolation='none', origin="upper", aspect="equal")

			for mask, cmap in zip(masks, cmaps):
				axarr[i,0].imshow(mask[x_slice, :, :], interpolation='none', origin="upper", aspect="equal", cmap=cmap, vmin=0, vmax=1.5)
				axarr[i,1].imshow(mask[:, y_slice, :], interpolation='none', origin="upper", aspect="equal", cmap=cmap, vmin=0, vmax=1.5)
				axarr[i,2].imshow(np.rot90(mask[:, :, z_slice], 3), interpolation='none', origin="upper", aspect="equal", cmap=cmap, vmin=0, vmax=1.5)

		for ax in axarr.flatten():
			ax.set(xticks=[], yticks=[])




# %%
bv = BrainViewer()
bv.get_structures()

#%%
sc_exps, sc_exps_ids = bv.get_structure_wt_experiments("SCm")
bv.view_multiple_experiments(sc_exps_ids)

#%%
bv.view_multiple_brain_regions(bv.structures.acronym.values, ["Reds", "Greens", "Blues", "Purples"])

#%%
