import pandas as pd
import numpy as np
import os


from brainrender.Utils.paths_manager import Paths



class Atlas(Paths):
	"""
	This class is the base structure for an Atlas class. Atlas-specific class will need to
    inherit from this class and re-define crucial methods to support scene creation.  
	"""

	atlas_name = "BASE"

    _root_midpoint = [None, None, None] # 3d coordinates of the CoM of root mesh

	def __init__(self, base_dir=None, **kwargs):
		""" 
		Set up file paths
		
		:param base_dir: path to directory to use for saving data (default value None)
		:param kwargs: can be used to pass path to individual data folders. See brainrender/Utils/paths_manager.py

		"""

		Paths.__init__(self, base_dir=base_dir, **kwargs)

        # Get some atlas specific data 
        # ! REPLACE these in the init method of your atlas
		self.annotated_volume = None # A 3d image with a scalar label at each region indicating
                                # which brain region each voxel corresponds to

		self.regions = None # list of all regions in the atlas
		self.region_acronyms = None # list of all regions' acronyms



	def print_structures(self):
		""" 
		Prints the name of every structure in the structure tree to the console.
		"""
		if isinstance(self.regions, list) and isinstance(self.region_acronyms, list):
            print([f"{a} - {n}" for a,n in zip(self.region_acronyms, self.regions)], sep="\n")

	# ---------------------------------------------------------------------------- #
	#                       Methods to support Scene creation                      #
	# ---------------------------------------------------------------------------- #
	"""
		These methods are used by brainrender.scene to populate a scene using
		the Allen brain atlas meshes. 
        You will need to overwrite these methods when you define your atlas class. 
        Not all methods are required for all atlases, but the fewer methods you have
        the less you can do with your atlas.
	"""

	# -------------------------- Getting regions/neurons ------------------------- #
	def _check_obj_file(self, structure, obj_file):
		"""
		If the .obj file for a brain region hasn't been downloaded/created already, 
        this function downloads it and saves it.

		:param structure: string, acronym of brain region
		:param obj_file: path to .obj file to save downloaded data.

		"""
		raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support
                    '_check_obj_file' method!")

	def _get_structure_mesh(self, acronym,  **kwargs):
		"""
		Fetches the mesh for a brain region from the Allen Brain Atlas SDK.

		:param acronym: string, acronym of brain region
		:param **kwargs:
		"""
		raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support
                    '_get_structure_mesh' method!")

	def get_region_unilateral(self, region, hemisphere="both", color=None, alpha=None):
		"""
		Regions meshes are loaded with both hemispheres' meshes by default.
		This function splits them in two.

		:param region: str, actors of brain region
		:param hemisphere: str, which hemisphere to return ['left', 'right' or 'both'] (Default value = "both")
		:param color: color of each side's mesh. (Default value = None)
		:param alpha: transparency of each side's mesh.  (Default value = None)

		"""
		raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support
                    'get_region_unilateral' method!")

	def add_neurons(self, neurons, display_soma_region=False, soma_regions_kwargs=None,
					display_axon_regions=False,
					display_dendrites_regions=False, **kwargs):
		"""
		Adds rendered morphological data of neurons reconstructions downloaded from the Mouse Light project at Janelia (or other sources). Can accept rendered neurons
		or a list of files to be parsed for rendering. Several arguments can be passed to specify how the neurons are rendered.

		:param neurons: str, list, dict. File(s) with neurons data or list of rendered neurons.
		:param display_soma_region: if True, the region in which the neuron's soma is located is rendered (Default value = False)
		:param soma_regions_kwargs: dict, specifies how the soma regions should be rendered (Default value = None)
		:param display_axon_regions: if True, the regions through which the axons go through are rendered (Default value = False)
		:param display_dendrites_regions: if True, the regions through which the dendrites go through are rendered  (Default value = False)
		:param **kwargs:
		"""
		raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support
                    'add_neurons' method!")
		
	# -------------------------- Parents and descendants ------------------------- #
	def get_structure_ancestors(self, regions, ancestors=True, descendants=False):
		"""
		Get's the ancestors of the region(s) passed as arguments

		:param regions: str, list of str with acronums of regions of interest
		:param ancestors: if True, returns the ancestors of the region  (Default value = True)
		:param descendants: if True, returns the descendants of the region (Default value = False)

		"""
		raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support
                    'get_structure_ancestors/get_structure_descendants' methods!")

	def get_structure_descendants(self, regions):
		return self.get_structure_ancestors(regions, ancestors=False, descendants=True)

	def get_structure_parent(self, acronyms):
		"""
		Gets the parent of a brain region (or list of regions) from the hierarchical structure of the
		Allen Brain Atals.

		:param acronyms: list of acronyms of brain regions.

		"""
		raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support
                    'get_structure_parent' method!")

	# ----------------------------------- Utils ---------------------------------- #
	def get_region_color(self, regions):
		"""
		Gets the RGB color of a brain region from the Allen Brain Atlas.

		:param regions:  list of regions acronyms.

		"""
		raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support
                    'get_structure_parent' method!")

	@staticmethod
	def _check_valid_region_arg(region):
		"""
		Check that the string passed is a valid brain region name.
		"""
		raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support
                    'get_structure_parent' method!")

	def get_hemispere_from_point(self, p0):
		if self._root_midpoint[0] is None:
			raise ValueError("The coordinates of the root's CoM are not specified for this atlas")
		if p0[2] > self._root_midpoint[2]:
			return 'right'
		else:
			return 'left'

	def get_structure_from_coordinates(self, p0, just_acronym=True):
		"""
		Given a point in the Allen Mouse Brain reference space, returns the brain region that the point is in. 

		:param p0: list of floats with XYZ coordinates. 

		"""
		raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support
                    'get_structure_from_coordinates' method!")
	
	def get_colors_from_coordinates(self, p0):
		"""
			Given a point or a list of points returns a list of colors where 
			each item is the color of the brain region each point is in
		"""
		raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support
                    'get_colors_from_coordinates' method!")


