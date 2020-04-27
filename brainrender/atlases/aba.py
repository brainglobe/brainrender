import pandas as pd
import numpy as np
import os

from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
from allensdk.api.queries.ontologies_api import OntologiesApi
from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
from allensdk.api.queries.tree_search_api import TreeSearchApi
from allensdk.core.reference_space_cache import ReferenceSpaceCache

from brainrender.Utils.paths_manager import Paths


class ABA(Paths):
	"""
	This class handles interaction with the Allen Brain Atlas datasets and APIs to get structure trees,
	experimental metadata and results, tractography data etc. 
	"""
	# useful vars for analysis    
	excluded_regions = ["fiber tracts"]
	resolution = 25

	_root_bounds = [[-17, 13193], 
				   [ 134, 7564], 
					[486, 10891]]

	_root_midpoint = [np.mean([-17, 13193]), 
						np.mean([134, 7564]),
						np.mean([486, 10891])]

	def __init__(self, projection_metric = "projection_energy", base_dir=None, **kwargs):
		""" 
		Set up file paths and Allen SDKs
		
		:param base_dir: path to directory to use for saving data (default value None)
		:param path_fiprojection_metricle: - str, metric to quantify the strength of projections from the Allen Connectome. (default value 'projection_energy')
		:param kwargs: can be used to pass path to individual data folders. See brainrender/Utils/paths_manager.py

		"""

		Paths.__init__(self, base_dir=base_dir, **kwargs)

		self.projection_metric = projection_metric

		# get mouse connectivity cache and structure tree
		self.mcc = MouseConnectivityCache(manifest_file=os.path.join(self.mouse_connectivity_cache, "manifest.json"))
		self.structure_tree = self.mcc.get_structure_tree()
		
		# get ontologies API and brain structures sets
		self.oapi = OntologiesApi()
		self.get_structures_sets()

		# get reference space
		self.space = ReferenceSpaceApi()
		self.spacecache = ReferenceSpaceCache(
			manifest=os.path.join(self.annotated_volume, "manifest.json"),  # downloaded files are stored relative to here
			resolution=self.resolution,
			reference_space_key="annotation/ccf_2017"  # use the latest version of the CCF
			)
		self.annotated_volume, _ = self.spacecache.get_annotation_volume()

		# mouse connectivity API [used for tractography]
		self.mca = MouseConnectivityApi()

		# Get tree search api
		self.tree_search = TreeSearchApi()

		# Get some metadata about experiments
		self.all_experiments = self.mcc.get_experiments(dataframe=True)
		self.strains = sorted([x for x in set(self.all_experiments.strain) if x is not None])
		self.transgenic_lines = sorted(set([x for x in set(self.all_experiments.transgenic_line) if x is not None]))


		# Store all regions metadata
		self.regions = self.other_sets["Structures whose surfaces are represented by a precomputed mesh"].sort_values('acronym')
		self.region_acronyms = list(self.other_sets["Structures whose surfaces are represented by a precomputed mesh"].sort_values(
											'acronym').acronym.values)

	# ---------------------------------------------------------------------------- #
	#                          STRUCTURE TREE INTERACTION                          #
	# ---------------------------------------------------------------------------- #

	# ------------------------- Get/Print structures sets ------------------------ #

	def get_structures_sets(self):
		""" 
		Get the Allen's structure sets.
		"""
		summary_structures = self.structure_tree.get_structures_by_set_id([167587189])  # main summary structures
		summary_structures = [s for s in summary_structures if s["acronym"] not in self.excluded_regions]
		self.structures = pd.DataFrame(summary_structures)

		# Other structures sets
		try:
			all_sets = pd.DataFrame(self.oapi.get_structure_sets())
		except:
			print("Could not retrieve data, possibly because there is no internet connection.")
		else:
			sets = ["Summary structures of the pons", "Summary structures of the thalamus", 
						"Summary structures of the hypothalamus", "List of structures for ABA Fine Structure Search",
						"Structures representing the major divisions of the mouse brain", "Summary structures of the midbrain", "Structures whose surfaces are represented by a precomputed mesh"]
			self.other_sets = {}
			for set_name in sets:
				set_id = all_sets.loc[all_sets.description == set_name].id.values[0]
				self.other_sets[set_name] = pd.DataFrame(self.structure_tree.get_structures_by_set_id([set_id]))

			self.all_avaliable_meshes = sorted(self.other_sets["Structures whose surfaces are represented by a precomputed mesh"].acronym.values)

	def print_structures_list_to_text(self):
		""" 
		Saves the name of every brain structure for which a 3d mesh (.obj file) is available in a text file.
		"""
		s = self.other_sets["Structures whose surfaces are represented by a precomputed mesh"].sort_values('acronym')
		with open('all_regions.txt', 'w') as o:
			for acr, name in zip(s.acronym.values, s['name'].values):
				o.write("({}) -- {}\n".format(acr, name))

	def print_structures(self):
		""" 
		Prints the name of every structure in the structure tree to the console.
		"""
		acronyms, names = self.structures.acronym.values, self.structures['name'].values
		sort_idx = np.argsort(acronyms)
		acronyms, names = acronyms[sort_idx], names[sort_idx]
		[print("({}) - {}".format(a, n)) for a,n in zip(acronyms, names)]

	# -------------------------- Parents and descendants ------------------------- #
	def get_structure_ancestors(self, regions, ancestors=True, descendants=False):
		"""
		Get's the ancestors of the region(s) passed as arguments

		:param regions: str, list of str with acronums of regions of interest
		:param ancestors: if True, returns the ancestors of the region  (Default value = True)
		:param descendants: if True, returns the descendants of the region (Default value = False)

		"""

		if not isinstance(regions, list):
			struct_id = self.structure_tree.get_structures_by_acronym([regions])[0]['id']
			return pd.DataFrame(self.tree_search.get_tree('Structure', struct_id, ancestors=ancestors, descendants=descendants))
		else:
			ancestors = []
			for region in regions:
				struct_id = self.structure_tree.get_structures_by_acronym([region])[0]['id']
				ancestors.append(pd.DataFrame(self.tree_search.get_tree('Structure', struct_id, ancestors=ancestors, descendants=descendants)))
			return ancestors

	def get_structure_descendants(self, regions):
		return self.get_structure_ancestors(regions, ancestors=False, descendants=True)

	def get_structure_parent(self, acronyms):
		"""
		Gets the parent of a brain region (or list of regions) from the hierarchical structure of the
		Allen Brain Atals.

		:param acronyms: list of acronyms of brain regions.

		"""
		if not isinstance(acronyms, list):
			self._check_valid_region_arg(acronyms)
			s = self.structure_tree.get_structures_by_acronym([acronyms])[0]
			if s['id'] in self.structures.id.values:
				return s
			else:
				return self.get_structure_ancestors(s['acronym']).iloc[-1]
		else:
			parents = []
			for region in acronyms:
				self._check_valid_region_arg(region)
				s = self.structure_tree.get_structures_by_acronym(acronyms)[0]

				if s['id'] in self.structures.id.values:
					parents.append(s)
				parents.append(self.get_structure_ancestors(s['acronym']).iloc[-1])
			return parents

	# ----------------------------------- Utils ---------------------------------- #
	def get_region_color(self, regions):
		"""
		Gets the RGB color of a brain region from the Allen Brain Atlas.

		:param regions:  list of regions acronyms.

		"""
		if not isinstance(regions, list):
			return self.structure_tree.get_structures_by_acronym([regions])[0]['rgb_triplet']
		else:
			return [self.structure_tree.get_structures_by_acronym([r])[0]['rgb_triplet'] for r in regions]

	@staticmethod
	def _check_valid_region_arg(region):
		"""
		Check that the string passed is a valid brain region name.

		:param region: string, acronym of a brain region according to the Allen Brain Atlas.

		"""
		if not isinstance(region, int) and not isinstance(region, str):
			raise ValueError("region must be a list, integer or string, not: {}".format(type(region)))
		else:
			return True

	def get_hemispere_from_point(self, p0):
		if p0[2] > self._root_midpoint[2]:
			return 'right'
		else:
			return 'left'

	def get_structure_from_coordinates(self, p0, just_acronym=True):
		"""
		Given a point in the Allen Mouse Brain reference space, returns the brain region that the point is in. 

		:param p0: list of floats with XYZ coordinates. 

		"""
		voxel = np.round(np.array(p0) / self.resolution).astype(int)
		try:
			structure_id = self.annotated_volume[voxel[0], voxel[1], voxel[2]]
		except:
			return None

		# Each voxel in the annotation volume is annotated as specifically as possible
		structure = self.structure_tree.get_structures_by_id([structure_id])[0]
		if structure is not None:
			if just_acronym:
				return structure['acronym']
		return structure
	
	def get_colors_from_coordinates(self, p0):
		"""
			Given a point or a list of points returns a list of colors where 
			each item is the color of the brain region each point is in
		"""
		if isinstance(p0[0], (float, int)):
			struct = self.get_structure_from_coordinates(p0, just_acronym=False)
			if struct is not None:
				return struct['rgb_triplet']
			else:
				return None
		else:
			structures = [self.get_structure_from_coordinates(p, just_acronym=False) for p in p0]
			colors = [struct['rgb_triplet'] if struct is not None else None 
							for struct in structures]
			return colors 


	# ---------------------------------------------------------------------------- #
	#                       CONNECTOME EXPERIMENT INTERACTION                      #
	# ---------------------------------------------------------------------------- #

	def load_all_experiments(self, cre=False):
		"""
		This function downloads all the experimental data from the MouseConnectivityCache and saves the unionized results
		as pickled pandas dataframes. The process is slow, but the ammount of disk space necessary to save the data is small,
		so it's worth downloading all the experiments at once to speed up subsequent analysis.

		:param cre: Bool - data from either wild time or cre mice lines (Default value = False)

		"""
		
		if not cre: raise NotImplementedError("Only works for wild type sorry")
		# Downloads all experiments from allen brain atlas and saves the results as an easy to read pkl file
		for acronym in self.structures.acronym.values:
			print("Fetching experiments for : {}".format(acronym))

			structure = self.structure_tree.get_structures_by_acronym([acronym])[0]
			experiments = self.mcc.get_experiments(cre=cre, injection_structure_ids=[structure['id']])

			print("     found {} experiments".format(len(experiments)))

			try:
				structure_unionizes = self.mcc.get_structure_unionizes([e['id'] for e in experiments], 
															is_injection=False,
															structure_ids=self.structures.id.values,
															include_descendants=False)
			except: pass
			structure_unionizes.to_pickle(os.path.join(self.output_data, "{}.pkl".format(acronym)))
	
	def experiments_source_search(self, SOI, *args, source=True,  **kwargs):
		"""
		Returns data about experiments whose injection was in the SOI, structure of interest

		:param SOI: str, structure of interest. Acronym of structure to use as seed for teh search
		:param *args: 
		:param source:  (Default value = True)
		:param **kwargs: 

		"""
		"""
			list of possible kwargs
				injection_structures : list of integers or strings
					Integer Structure.id or String Structure.acronym.
				target_domain : list of integers or strings, optional
					Integer Structure.id or String Structure.acronym.
				injection_hemisphere : string, optional
					'right' or 'left', Defaults to both hemispheres.
				target_hemisphere : string, optional
					'right' or 'left', Defaults to both hemispheres.
				transgenic_lines : list of integers or strings, optional
					Integer TransgenicLine.id or String TransgenicLine.name. Specify ID 0 to exclude all TransgenicLines.
				injection_domain : list of integers or strings, optional
					Integer Structure.id or String Structure.acronym.
				primary_structure_only : boolean, optional
				product_ids : list of integers, optional
					Integer Product.id
				start_row : integer, optional
					For paging purposes. Defaults to 0.
				num_rows : integer, optional
					For paging purposes. Defaults to 2000.

		"""
		transgenic_id = kwargs.pop('transgenic_id', 0) # id = 0 means use only wild type
		primary_structure_only = kwargs.pop('primary_structure_only', True)

		if not isinstance(SOI, list): SOI = [SOI]

		if source:
			injection_structures=SOI
			target_domain = None
		else:
			injection_structures = None
			target_domain = SOI

		return pd.DataFrame(self.mca.experiment_source_search(injection_structures=injection_structures,
											target_domain = target_domain,
											transgenic_lines=transgenic_id,
											primary_structure_only=primary_structure_only))

	def experiments_target_search(self, *args, **kwargs):
		"""

		:param *args: 
		:param **kwargs: 

		"""
		return self.experiments_source_search(*args, source=False, **kwargs)

	def fetch_experiments_data(self, experiments_id, *args, average_experiments=False, **kwargs):
		"""
		Get data and metadata for expeirments in the Allen Mouse Connectome project. 
	
		:param experiments_id: int, list, np.ndarray with ID of experiments whose data need to be fetched
		:param *args: 
		:param average_experiments:  (Default value = False)
		:param **kwargs: 

		"""
		if isinstance(experiments_id, np.ndarray):
			experiments_id = [int(x) for x in experiments_id]
		elif not isinstance(experiments_id, list): 
			experiments_id = [experiments_id]
		if [x for x in experiments_id if not isinstance(x, int)]:
			raise ValueError("Invalid experiments_id argument: {}".format(experiments_id))

		default_structures_ids = self.structures.id.values


		is_injection = kwargs.pop('is_injection', False) # Include only structures that are not injection
		structure_ids = kwargs.pop('structure_ids', default_structures_ids) # Pass IDs of structures of interest 
		hemisphere_ids= kwargs.pop('hemisphere_ids', None) # 1 left, 2 right, 3 both

		if not average_experiments:
			return pd.DataFrame(self.mca.get_structure_unionizes(experiments_id,
												is_injection = is_injection,
												structure_ids = structure_ids,
												hemisphere_ids = hemisphere_ids))
		else:
			raise NotImplementedError("Need to find a way to average across experiments")
			unionized = pd.DataFrame(self.mca.get_structure_unionizes(experiments_id,
												is_injection = is_injection,
												structure_ids = structure_ids,
												hemisphere_ids = hemisphere_ids))

		for regionid in list(set(unionized.structure_id)):
			region_avg = unionized.loc[unionized.structure_id == regionid].mean(axis=1) ## UNUSED!!??

	####### ANALYSIS ON EXPERIMENTAL DATA
	def analyze_efferents(self, ROI, projection_metric = None):
		"""
		Loads the experiments on ROI and looks at average statistics of efferent projections

		:param ROI: str, acronym of brain region of interest
		:param projection_metric: if None, the default projection metric is used, otherwise pass a string with metric to use (Default value = None)

		"""
		if projection_metric is None: 
			projection_metric = self.projection_metric

		experiment_data = pd.read_pickle(os.path.join(self.output_data, "{}.pkl".format(ROI)))
		experiment_data = experiment_data.loc[experiment_data.volume > self.volume_threshold]

		# Loop over all structures and get the injection density
		results = {"left":[], "right":[], "both":[], "id":[], "acronym":[], "name":[]}
		for target in self.structures.id.values:
			target_acronym = self.structures.loc[self.structures.id == target].acronym.values[0]
			target_name = self.structures.loc[self.structures.id == target].name.values[0]

			exp_target = experiment_data.loc[experiment_data.structure_id == target]

			exp_target_hemi = self.hemispheres(exp_target.loc[exp_target.hemisphere_id == 1], 
												exp_target.loc[exp_target.hemisphere_id == 2], 
												exp_target.loc[exp_target.hemisphere_id == 3])
			proj_energy = self.hemispheres(np.nanmean(exp_target_hemi.left[projection_metric].values),
											np.nanmean(exp_target_hemi.right[projection_metric].values),
											np.nanmean(exp_target_hemi.both[projection_metric].values)
			)


			for hemi in self.hemispheres_names:
				results[hemi].append(proj_energy._asdict()[hemi])
			results["id"].append(target)
			results["acronym"].append(target_acronym)
			results["name"].append(target_name)

		results = pd.DataFrame.from_dict(results).sort_values("right", na_position = "first")
		return results

	def analyze_afferents(self, ROI, projection_metric = None):
		"""[Loads the experiments on ROI and looks at average statistics of afferent projections]

		:param ROI: str, acronym of region of itnerest
		:param projection_metric: if None, the default projection metric is used, otherwise pass a string with metric to use (Default value = None)

		"""
		if projection_metric is None: 
			projection_metric = self.projection_metric
		ROI_id = self.structure_tree.get_structures_by_acronym([ROI])[0]["id"] ## UNUSED!!??

		# Loop over all strctures and get projection towards SOI
		results = {"left":[], "right":[], "both":[], "id":[], "acronym":[], "name":[]}

		for origin in self.structures.id.values:
			origin_acronym = self.structures.loc[self.structures.id == origin].acronym.values[0]
			origin_name = self.structures.loc[self.structures.id == origin].name.values[0]

			experiment_data = pd.read_pickle(os.path.join(self.output_data, "{}.pkl".format(origin_acronym)))
			experiment_data = experiment_data.loc[experiment_data.volume > self.volume_threshold]

			exp_target = experiment_data.loc[experiment_data.structure_id == SOI_id] ## BUG! SOI_id is not defined
			exp_target_hemi = self.hemispheres(exp_target.loc[exp_target.hemisphere_id == 1], exp_target.loc[exp_target.hemisphere_id == 2], exp_target.loc[exp_target.hemisphere_id == 3])
			proj_energy = self.hemispheres(np.nanmean(exp_target_hemi.left[projection_metric].values),
											np.nanmean(exp_target_hemi.right[projection_metric].values),
											np.nanmean(exp_target_hemi.both[projection_metric].values)
			)
			for hemi in self.hemispheres_names:
				results[hemi].append(proj_energy._asdict()[hemi])
			results["id"].append(origin)
			results["acronym"].append(origin_acronym)
			results["name"].append(origin_name)

		results = pd.DataFrame.from_dict(results).sort_values("right", na_position = "first")
		return results

	####### GET TRACTOGRAPHY AND SPATIAL DATA
	def get_projection_tracts_to_target(self, p0=None, **kwargs):
		"""
		Gets tractography data for all experiments whose projections reach the brain region or location of iterest.
		
		:param p0: list of 3 floats with XYZ coordinates of point to be used as seed (Default value = None)
		:param **kwargs: 
		"""

		# check args
		if p0 is None:
			raise ValueError("Please pass coordinates")
		elif isinstance(p0, np.ndarray):
			p0 = list(p0)
		elif not isinstance(p0, (list, tuple)):
			raise ValueError("Invalid argument passed (p0): {}".format(p0))

		tract = self.mca.experiment_spatial_search(seed_point=p0, **kwargs)

		if isinstance(tract, str): 
			raise ValueError('Something went wrong with query, query error message:\n{}'.format(tract))
		else:
			return tract
