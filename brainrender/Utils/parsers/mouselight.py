import sys
sys.path.append('./')

import os
import json
from vtkplotter import *

import pandas as pd
import numpy as np
from functools import partial
from collections import namedtuple

import allensdk.core.swc as allen_swc

from brainrender.Utils.data_io import load_json, listdir
from brainrender.Utils.data_manipulation import get_coords, mirror_actor_at_point
from brainrender.colors import *
from brainrender import *

from brainrender.Utils.paths_manager import Paths


class NeuronsParser(Paths):
	""" 
		Takes care of parsing neuron's morphology data from different formats (.json, .swc) and rendering them as vtk actors. 
		Supports various ways to specify how things should be rendered and classes to edit/modify rendered neurons. 
		Also saves and loads the results of parsing. 
	"""
	def __init__(self, scene=None, 
				render_neurites = True, mirror=False, 
				neurite_radius=None, color_by_region=False, force_to_hemisphere=None, base_dir=None,
				color_neurites=True, axon_color=None, soma_color=None, dendrites_color=None, random_color=False, **kwargs):
		"""
		Set up variables used for rendering

		:param scene: instance of class brainrender.Scene (Default value = None)
		:param render_neurites: Bool, If true, axons and dendrites are rendered (Default value = True)
		:param neurite_radius: float with radius of axons and dendrites. If None default is used. (Default value = None)
		:param color_neurites: Bool, if True axons and neurites are colored differently from the soma (Default value = True)
		:param mirror: Bool if True neurons are mirrored so that there is a version in each hemisphere (Default value = None)
		:param soma_color: soma_color color of the neurons' soma. Also used for neurites if they are not to be colored differently (Default value = None)
		:param axon_color: color of the neurons' axon. If none or False, the soma's color is used. (Default value = None)
		:param dendrites_color: color of the neurons' dendrites. If none or False, the soma's color is used.(Default value = None)
		:param random_color: Bool, if True a random color is used for each neuron.  (Default value = False)
		:param color_by_region: bool, if True, neurons are colored according to the Allen Brain Atlas color for the region the soma is in.  (Default value = False)
		:param force_to_hemisphere: str, if 'left' or 'right' neurons are rendered in the selected hemisphere, if False or None they are rendered in the original hemisphere.  (Default value = None)
		:param base_dir: path to directory to use for saving data (default value None)
		:param kwargs: can be used to pass path to individual data folders. See brainrender/Utils/paths_manager.py

		"""
		self.scene = scene # for the meaning of the arguments check self.render_neurons
		self.render_neurites = render_neurites 
		self.neurite_radius = neurite_radius 
		self.color_neurites = color_neurites 
		self.axon_color = axon_color 
		self.soma_color = soma_color 
		self.dendrites_color = dendrites_color 
		self.random_color = random_color
		self.mirror = mirror
		self.color_by_region = color_by_region
		self.force_to_hemisphere = force_to_hemisphere

		Paths.__init__(self, base_dir=base_dir, **kwargs)

	def render_neurons(self, ml_file, **kwargs):
		"""
		Given a file with JSON data about neuronal structures downloaded from the Mouse Light neurons browser website,
		this function creates VTKplotter actors that can be used to render the neurons, returns them as nested dictionaries.

		:param ml_file: str, path to a JSON file with neurons data
		:param **kwargs: see kwargs of NeuronsParser.__init__
		:returns: actors [list] -- [list of dictionaries, each dictionary contains the VTK actors of one neuron]

		"""

		# parse options
		if "scene" in list(kwargs.keys()):
			self.scene = kwargs['scene']
		if "render_neurites" in list(kwargs.keys()):
			self.render_neurites = kwargs['render_neurites']
		if "neurite_radius" in list(kwargs.keys()):
			self.neurite_radius = kwargs['neurite_radius']
		if "color_neurites" in list(kwargs.keys()):
			self.color_neurites = kwargs['color_neurites']
		if "axon_color" in list(kwargs.keys()):
			self.axon_color = kwargs['axon_color']
		if "soma_color" in list(kwargs.keys()):
			self.soma_color = kwargs['soma_color']
		if "dendrites_color" in list(kwargs.keys()):
			self.dendrites_color = kwargs['dendrites_color']
		if "random_color" in list(kwargs.keys()):
			self.random_color = kwargs['random_color']
		if "mirror" in list(kwargs.keys()):
			self.mirror = kwargs['mirror']
		if "force_to_hemisphere" in list(kwargs.keys()):
			self.force_to_hemisphere = kwargs['force_to_hemisphere']
		if 'color_by_region' in list(kwargs.keys()):
			self.color_by_region = kwargs['color_by_region']

		self.rendering_necessary = True # It won't be if we are dealing with a list of Allen .swc files

		# if mirror get mirror coordinates
		if self.mirror:
			self.mirror_coord = self.scene.get_region_CenterOfMass('root', unilateral=False)[2]
		else:
			self.mirror_coord = False
		self.mirror_ax = 'x'

		# Check neurite radius
		if self.neurite_radius is None:
			neurite_radius = DEFAULT_NEURITE_RADIUS
		
		# Load the data
		if isinstance(ml_file, (tuple, list)):
			checkfile = ml_file[0]
			is_iter = True
			neurons_names = [os.path.split(f)[-1].split(".")[0] for f in ml_file]
		else:
			checkfile = ml_file
			is_iter = False
			neurons_names = [os.path.split(ml_file)[-1].split(".")[0]]

		if ".swc" in checkfile.lower():
			self.is_json = False
			data = self.handle_parsing_swc(ml_file, is_iter)
		else:
			self.is_json = True
			if not is_iter:
				data = load_json(checkfile)
				data = data["neurons"]
			else:
				data = []
				for f in ml_file:
					fdata = load_json(f)
					data.extend(fdata['neurons'])

		if not self.rendering_necessary:
			return self.actors, self.regions
		else:	
			# Render neurons
			self.n_neurons  = len(data)
			self.actors, self.regions = [], []

			if len(neurons_names) < self.n_neurons: 
				name = neurons_names[0]
				neurons_names = [name+"_{}".format(i) for i in range(self.n_neurons)]

			# Loop over neurons
			for nn, neuron in enumerate(data):
				neuron_actors, soma_region = self.render_neuron(neuron, nn, neurons_names[nn])
				self.actors.append(neuron_actors); self.regions.append(soma_region)
			return self.actors, self.regions

	def _render_neuron_get_params(self, neuron_number, neuron=None, soma_region=None, soma=None):
		"""
		Makes sure that all the parameters to specify how neurons should be rendered. 

		:param neuron_number: number of the neuron being rendered
		:param neuron: neuron's metadata (Default value = None)
		:param soma_region: str with the acronym of the region the soma is in (Default value = None)
		:param soma: list with XYZ coordinates of the neuron's soma. (Default value = None)

		"""
		# Define colors of different components
		if not self.color_by_region:
			if self.random_color:
				if not isinstance(self.random_color, str):
					color = get_random_colors(n_colors=1)
				else: # random_color is a colormap 
					color = colorMap(neuron_number, name=self.random_color, vmin=0, vmax=self.n_neurons)
				axon_color = soma_color = dendrites_color = color
			else:
				if self.soma_color is None:
					soma_color = get_random_colors(n_colors=1)

				if not self.color_neurites:
					axon_color = dendrites_color = soma_color = self.soma_color
				else:
					soma_color = self.soma_color
					if self.axon_color is None:
						axon_color = soma_color
					else:
						axon_color = self.axon_color
					if self.dendrites_color is None:
						dendrites_color = soma_color
					else:
						dendrites_color = self.dendrites_color

			# check that the colors make sense
			if not check_colors([soma_color, axon_color, dendrites_color]):
				raise ValueError("The colors chosen are not valid: soma - {}, dendrites {}, axon {}".format(soma_color, dendrites_color, axon_color))

			# check if we have lists of colors or single colors
			if isinstance(soma_color, list):
				if isinstance(soma_color[0], str) or isinstance(soma_color[0], list):
					soma_color = soma_color[neuron_number]
			if isinstance(dendrites_color, list):
				if isinstance(dendrites_color[0], str) or isinstance(dendrites_color[0], list):
					dendrites_color = dendrites_color[neuron_number]
			if isinstance(axon_color, list):
				if isinstance(axon_color[0], str) or isinstance(axon_color[0], list):
					axon_color = axon_color[neuron_number]                

		# get allen info: it containes the allenID of each brain region
		# each sample has the corresponding allen ID so we can recontruct in which brain region it is
		if neuron is not None:
			if 'allenInformation' in list(neuron.keys()):
				self.alleninfo = pd.DataFrame(neuron['allenInformation'])             # get brain structure in which is the soma
				soma_region = self.scene.get_structure_parent(self.alleninfo.loc[self.alleninfo.allenId == neuron['soma']['allenId']].acronym.values[0])['acronym']
			else:
				self.alleninfo = None
				soma_region = self.scene.get_structure_from_coordinates(get_coords(neuron['soma']))
				if soma_region is not None:
					soma_region = soma_region['acronym']
		elif soma_region is None:
			self.alleninfo = None
			if soma is not None:
				soma_region = self.scene.get_structure_from_coordinates(get_coords(soma))
				if soma_region is not None:
					soma_region = soma_region['acronym']
			else:
				raise ValueError("You need to pass either a neuron, or a soma region or a soma")
		else:
			self.alleninfo = None

		if soma_region is not None:
			soma_region = self.scene.get_structure_parent(soma_region)['acronym']
		else:
			soma_region = "root"

		if self.color_by_region:
			try:
				region_color = self.scene.structure_tree.get_structures_by_acronym([soma_region])[0]['rgb_triplet']
			except:
				print("could not find default color for region: {}. Using random color instead".format(soma_region))
				region_color = get_random_colors(n_colors=1)

			axon_color = soma_color = dendrites_color = region_color

		return soma_color, axon_color, dendrites_color, soma_region

	def render_neuron(self, neuron, neuron_number, neuron_name):
		"""
		This function takes care of rendering a single neuron.

		:param neuron: dictionary with neurons data
		:param neuron_number: number of neuron being rendered
		:param neuron_name: name of the neuron, used to load/save the .vtk files with the rendered neuron.

		"""
		# Prepare variables for rendering
		soma_color, axon_color, dendrites_color, soma_region =  self._render_neuron_get_params(neuron_number, neuron=neuron)
		
		# create soma actor
		neuron_actors = None
		if USE_MORPHOLOGY_CACHE:
			neuron_actors = self._load_cached_neuron(neuron_name)
			if neuron_actors is not None:
				for component, color in zip(['soma', 'dendrites', 'axon'], [soma_color, dendrites_color, axon_color]):
					if component in list(neuron_actors.keys()):
						neuron_actors[component].color(color)
				return neuron_actors, {'soma':soma_region, 'dendrites':None, 'axons':None}

		if not USE_MORPHOLOGY_CACHE or neuron_actors is None:
			neuron_actors = {}

			self.soma_coords = get_coords(neuron["soma"], mirror=self.mirror_coord, mirror_ax=self.mirror_ax)
			neuron_actors['soma'] = Sphere(pos=self.soma_coords, c=soma_color, r=SOMA_RADIUS)

			# Draw dendrites and axons
			if self.render_neurites:
				if self.is_json:
					neuron_actors['dendrites'], dendrites_regions = self.neurites_parser(pd.DataFrame(neuron["dendrite"]), dendrites_color)
					neuron_actors['axon'], axon_regions = self.neurites_parser(pd.DataFrame(neuron["axon"]), axon_color)
				else:
					neuron_actors['dendrites'], dendrites_regions = self.neurites_parser_swc(pd.DataFrame(neuron["dendrite"]), dendrites_color)
					neuron_actors['axon'], axon_regions = self.neurites_parser_swc(pd.DataFrame(neuron["axon"]), axon_color)
			else:
				neuron_actors['dendrites'], dendrites_regions = [], None
				neuron_actors['axon'], axon_regions = [], None

			self.decimate_neuron_actors(neuron_actors)
			self.smooth_neurons(neuron_actors)

			# force to hemisphere
			if self.force_to_hemisphere is not None:
					neuron_actors = self.mirror_neuron(neuron_actors)

			if USE_MORPHOLOGY_CACHE:
				self._cache_neuron(neuron_actors, neuron_name)

			return neuron_actors, {'soma':soma_region, 'dendrites':dendrites_regions, 'axon':axon_regions}
		
	def _cache_neuron(self, neuron_actors, neuron_name):
		"""
		Save a loaded neuron

		:param neuron_actors: list of neuron's actors
		:param neuron_name: name of the neuron

		"""
		if not neuron_name or neuron_name is None: return
		for neurite, actor in neuron_actors.items():
			if actor is None: continue
			fl = os.path.join(self.morphology_cache, neuron_name+"_"+neurite+".vtk")
			if isinstance(actor, list):
				if not actor: continue
				else:
					raise ValueError("Something went wrong while saving the actor")
			actor.write(fl)

	def _load_cached_neuron(self, neuron_name):
		"""
		Load a cached neuron's VTK actors

		:param neuron_name: str with neuron name

		"""
		if not neuron_name or neuron_name is None:
			return None

		if self.render_neurites:
			allowed_components = ['soma', 'axon', 'dendrites']
			skipped_components = []
		else:
			allowed_components = ['soma']
			skipped_components = ['axon', 'dendrites']

		neuron_files = [f for f in listdir(self.morphology_cache) if neuron_name in f]
		if not neuron_files: return None
		else:
			neuron_actors = {}
			for f in neuron_files:
				component = os.path.split(f)[-1].split(".")[0].split("_")[-1]
				if component not in allowed_components and component not in skipped_components:
					raise ValueError("Weird file name, unsure what to do: {}".format(f))
				elif component not in allowed_components and component in skipped_components:
					continue
				neuron_actors[component] = load(f)
			return neuron_actors

	def mirror_neuron(self, neuron_actors):
		"""
		Mirror over the sagittal plane between the two hemispheres.

		:param neuron_actors: list of actors for one neuron.

		"""
		def _mirror_neuron(neuron, mcoord):
			"""
			Actually takes care of mirroring a neuron

			:param neuron: neuron's meshes
			:param mcoord: coordinates of the point to use for the mirroring

			"""
			# This function does the actual mirroring
			for name, actor in neuron.items():
				# get mesh points coords and shift them to other hemisphere
				if isinstance(actor, (list, tuple, str)) or actor is None:
					continue
				neuron[name] = mirror_actor_at_point(actor, mcoord, axis='x')
			return neuron

		# Makes sure that the neuron is in the desired hemisphere
		mirror_coor = self.scene.get_region_CenterOfMass('root', unilateral=False)[2]

		if self.force_to_hemisphere.lower() == "left":
			if self.soma_coords[2] > mirror_coor:
				neuron_actors = self._mirror_neuron(neuron_actors, mirror_coor)
		elif self.force_to_hemisphere.lower() == "right":
			if self.soma_coords[2] < mirror_coor:
				neuron_actors = self._mirror_neuron(neuron_actors, mirror_coor)
		else:
			raise ValueError("unrecognised argument for force to hemisphere: {}".format(self.force_to_hemisphere))
		return neuron_actors



	@staticmethod
	def decimate_neuron_actors(neuron_actors):
		"""
		Can be used to decimate the VTK actors for the neurons (i.e. reduce number of polygons). Should make the rendering faster.

		:param neuron_actors: list of actors for a neuron

		"""
		if DECIMATE_NEURONS:
			for k, actors in neuron_actors.items():
				if not isinstance(actors, list):
					actors.decimate()
				else:
					for actor in actors:
						actor.decimate() 

	@staticmethod
	def smooth_neurons(neuron_actors):
		"""
		Can be used to smooth the VTK actors for the neurons. Should improve apect of neurons

		:param neuron_actors: list of actors for a neuron

		"""
		if SMOOTH_NEURONS:
			for k, actors in neuron_actors.items():
				if actors is None: continue
				if not isinstance(actors, list):
					actors.smoothLaplacian()
				else:
					for actor in actors:
						actor.smoothLaplacian()

	def _get_neurites_radius(self):
		""" 
			Get the neurites radius parameter
		"""
		if self.neurite_radius is None:
			return DEFAULT_NEURITE_RADIUS
		else:
			return self.neurite_radius

	def neurites_parser(self, neurites, color):
		"""
		Given a dataframe with all the samples for some neurites, create "Tube" actors that render each neurite segment.	
		----------------------------------------------------------------
		This function works by first identifyingt the branching points of a neurite structure. Then each segment between either two branchin points
		or between a branching point and a terminal is modelled as a Tube. This minimizes the number of actors needed to represent the neurites
		while stil accurately modelling the neuron.
		
		Known issue: the axon initial segment is missing from renderings.

		:param neurites: dataframe with each sample for the neurites
		:param color: color to be assigned to the Tube actor

		
		"""
		neurite_radius = self._get_neurites_radius()

		# get branching points
		try:
			parent_counts = neurites["parentNumber"].value_counts()
		except:
			if len(neurites) == 0:
				print("Couldn't find neurites data")
				return [], []
			else:
				raise ValueError("Something went wrong while rendering neurites:\n{}".format(neurites))
		branching_points = parent_counts.loc[parent_counts > 1]

		# loop over each branching point
		actors = []
		for idx, bp in branching_points.iteritems():
			# get neurites after the branching point
			bp = neurites.loc[neurites.sampleNumber == idx]
			post_bp = neurites.loc[neurites.parentNumber == idx]
			
			# loop on each branch after the branching point
			for bi, branch in post_bp.iterrows():
				if bi == 0:
					branch_points = [self.soma_coords, get_coords(bp, mirror=self.mirror_coord, mirror_ax=self.mirror_ax), get_coords(branch, mirror=self.mirror_coord, mirror_ax=self.mirror_ax)] # this list stores all the samples that  are part of a branch
				else:
					branch_points = [get_coords(bp, mirror=self.mirror_coord, mirror_ax=self.mirror_ax), get_coords(branch, mirror=self.mirror_coord, mirror_ax=self.mirror_ax)] 

				# loop over all following points along the branch, until you meet either a terminal or another branching point. store the points
				idx = branch.sampleNumber
				while True:
					nxt = neurites.loc[neurites.parentNumber == idx]
					if len(nxt) != 1: 
						break
					else:
						branch_points.append(get_coords(nxt, mirror=self.mirror_coord, mirror_ax=self.mirror_ax))
						idx += 1

				# if the branch is too short for a tube, create a sphere instead
				if len(branch_points) < 2: # plot either a line between two branch_points or  a spheere
					actors.append(Sphere(branch_points[0], c="g", r=100))
					continue 
				
				# create tube actor
				actors.append(shapes.Tube(branch_points, r=neurite_radius, c=color, alpha=1, res=NEURON_RESOLUTION))
		
		# merge actors' meshes to make rendering faster
		merged = merge(*actors)
		if merged is None:
			return None, None
		merged.color(color)

		# get regions the neurites go through
		regions = []
		if "allenId" in neurites.columns:
			for rid in set(neurites.allenId.values):
				try:
					region = self.alleninfo.loc[self.alleninfo.allenId == rid].acronym.values[0]
					regions.append(self.scene.get_structure_parent(region)['acronym'])
				except:
					pass

		return merged, regions

	def neurites_parser_swc(self, neurites, color):
		"""
		Parses neuron's  neurites when the data are provided as .swc

		:param neurites: datafarme with neurites samples 
		:param color: color for vtk actor

		"""
		coords = [self.soma_coords]
		coords.extend([get_coords(sample, mirror=self.mirror_coord, mirror_ax=self.mirror_ax) for i, sample in neurites.iterrows()])
		lines = Spheres(coords, r=38, c=color, res=4)
		regions = []
		return lines, regions

	def filter_neurons_by_region(self, neurons, regions, neurons_regions=None):
		"""
		Only returns neurons whose soma is in one of the regions in regions

		:param neurons: list of neurons
		:param regions: list of regions
		:param neurons_regions: list of regions each neuron is in (Default value = None)

		"""

		if not isinstance(neurons, list): neurons = [neurons]
		if not isinstance(regions, list): regions = [regions]
		if neurons_regions is not None:
			if not isinstance(neurons_regions, list):
				neurons_regions = [neurons_regions]

		keep = []
		for i, neuron in enumerate(neurons):
			if neurons_regions is None:
				try:
					coords = neuron['soma'].centerOfMass()
				except: raise ValueError(neuron)
				region = self.scene.get_region_from_point(coords)
			else:
				if isinstance(neurons_regions[0], dict):
					region = neurons_regions[i]['soma']
				else:
					region = neurons_regions[i]

			if region is None: 
				continue
			elif region in regions:
				keep.append(neuron)
			else:
				continue

		return keep

	def parse_neurons_swc_allen(self, morphology, neuron_number):
		"""
		SWC parser for Allen neuron's morphology data, they're a bit different from the Mouse Light SWC

		:param morphology: data with morphology
		:param neuron_number: int, number of the neuron being rendered.

		"""
		# Get params
		neurite_radius = self._get_neurites_radius()
		soma_color, axon_color, dendrites_color, soma_region =  \
			self._render_neuron_get_params(neuron_number, soma=morphology.soma)

		# Create soma actor
		neuron_actors, regions = {"soma":None, "axon":[], "dendrites":[]}, {'soma':soma_region, 'dendrites':[], 'axon':[]}
		neuron_actors['soma'] = Sphere(pos=get_coords(morphology.soma)[::-1], 
										c=soma_color, r=SOMA_RADIUS)

		# loop over trees
		if self.render_neurites:
			for tree in morphology._tree_list:
				tree = pd.DataFrame(tree)

				# get node numbers in t
				# get the first non soma node
				first_node_type = tree.loc[tree.type != morphology.SOMA].type.values[0]

				# get the branch type
				if first_node_type == morphology.AXON:
					neurite = "axon"
					color = axon_color
				else:
					neurite = "dendrites"
					color = dendrites_color
				
				# Get all the points that make the branch
				branch_points = [[x, y, z] for x, y, z in zip(tree.x.values, tree.y.values, tree.z.values)]

				# Create actor
				neuron_actors[neurite].append(\
					shapes.Tube(branch_points, r=neurite_radius, 
							c=color, alpha=1, res=NEURON_RESOLUTION))

			# merge actors' meshes to make rendering faster
			for neurite, color in zip(["axon", "dendrites"], [axon_color, dendrites_color]):
				if neuron_actors[neurite]:
					neuron_actors[neurite] = merge(*neuron_actors[neurite])
					neuron_actors[neurite].color(color)

		self.decimate_neuron_actors(neuron_actors)
		self.smooth_neurons(neuron_actors)

		# force to hemisphere
		if self.force_to_hemisphere is not None:
				neuron_actors = self.mirror_neuron(neuron_actors)

		# Check output
		if not neuron_actors["axon"]: neuron_actors["axon"] = None
		if not neuron_actors["dendrites"]: neuron_actors["dendrites"] = None

		return neuron_actors, regions

	def parse_neuron_swc(self, filepath, neuron_number):
		"""
		Given an swc file, render the neuron

		:param filepath: str with path to swc file
		:param neuron_number: numnber of neuron being rendered

		"""
		# details on swc files: http://www.neuronland.org/NLMorphologyConverter/MorphologyFormats/SWC/Spec.html
		_sample = namedtuple("sample", "sampleN structureID x y z r parent") # sampleN structureID x y z r parent

		# in json {'allenId': 1021, 'parentNumber': 5, 'radius': 0.5, 'sampleNumber': 6, 
		# 'structureIdentifier': 2, 'x': 6848.52419500001, 'y': 2631.9816355, 'z': 3364.3552898125}
		
		if not os.path.isfile(filepath) or not ".swc" in filepath.lower(): raise ValueError("unrecognized file path: {}".format(filepath))

		try:
			morphology = allen_swc.read_swc(filepath)
			return self.parse_neurons_swc_allen(morphology, neuron_number)
		except:
			pass #  the .swc file fas not generate with by allen

		f = open(filepath)
		content = f.readlines()
		f.close()

		# crate empty dicts for soma axon and dendrites
		data = {'soma':     dict(allenId=[], parentNumber=[], radius=[], sampleNumber=[], x=[], y=[], z=[]),
				'axon':     dict(allenId=[], parentNumber=[], radius=[], sampleNumber=[], x=[], y=[], z=[]),
				'dendrite': dict(allenId=[], parentNumber=[], radius=[], sampleNumber=[], x=[], y=[], z=[])}

		# start looping around samples
		for sample in content:
			if sample[0] == '#': 
				continue # skip comments
			s = _sample(*[float(samp.replace("\n", "")) for samp in sample.split("\t")])

			# what structure is this
			if s.structureID in [1., -1.]: key = "soma"
			elif s.structureID in [2.]: key = 'axon'
			elif s.structureID in [3., 4.]: key = 'dendrite'
			else:
				raise ValueError("unrecognised sample in SWC file: {}".format(s))

			# append data to dictionary
			data[key]['parentNumber'].append(int(s.parent))
			data[key]['radius'].append(s.r)
			data[key]['x'].append(s.x)
			data[key]['y'].append(s.y)
			data[key]['z'].append(s.z)
			data[key]['sampleNumber'].append(int(s.sampleN))
			data[key]['allenId'].append(-1) # TODO get allen ID from coords

		return data

	def handle_parsing_swc(self, swc_files, is_iter):
		"""
			Takes care of handling the case in which one or multiple SWC files are passed.
			Which renderer and what is returned varies depending on the source of the SWC, so this
			function hadles this variable outcomes.

		:param swc_files: list of swc files
		:param is_iter: 

		"""
		if not is_iter:
			res = self.parse_neuron_swc(swc_files, 0)
			if len(res) == 1:
				return [res]
			else:
				self.actors, self.regions = [res[0]], res[1]
				self.rendering_necessary = False
				return None

		else:
			# ? Render multiple SWC files
			self.n_neurons = len(swc_files)

			# render
			data = [self.parse_neuron_swc(f, i) for i, f in enumerate(swc_files)]

			# Check outcome
			if len(data[0]) == 1:
				return data
			else:
				self.actors, self.regions = [d[0] for d in data], [d[1] for d in data]
				self.rendering_necessary = False


def edit_neurons(neurons, **kwargs):
	"""
		Modify neurons actors after they have been created, at render time.
		neurons should be a list of dictionaries with soma, dendrite and axon actors of each neuron.

	:param neurons: list of dictionaries with vtk actors for each neuron
	:param **kwargs: 

	"""
	soma_color, axon_color, dendrites_color = None, None, None
	for neuron in neurons:
		if "random_color" in kwargs:
			if kwargs["random_color"]:
				if not isinstance(kwargs["random_color"], str):
					color = get_random_colors(n_colors=1)
				else: # random_color is a colormap 
					color = colorMap(np.random.randint(1000), name=kwargs["random_color"], vmin=0, vmax=1000)
				axon_color = soma_color = dendrites_color = color
		elif "color_neurites" in kwargs:
			soma_color = neuron["soma"].color()
			if not kwargs["color_neurites"]:
				axon_color = dendrites_color = soma_color
			else:
				if not "axon_color" in kwargs:
					# print("no axon color provided, using somacolor")
					axon_color = soma_color
				else:
					axon_color = kwargs["axon_color"]

				if not "dendrites_color" in kwargs:
					# print("no dendrites color provided, using somacolor")
					dendrites_color = soma_color
				else:
					dendrites_color = kwargs["dendrites_color"]
		elif "soma_color" in kwargs:
			if check_colors(kwargs["soma_color"]):
				soma_color = kwargs["soma_color"]
			else: 
				print("Invalid soma color provided")
				soma_color = neuron["soma"].color()
		elif "axon_color" in kwargs:
			if check_colors(kwargs["axon_color"]):
				axon_color = kwargs["axon_color"]
			else: 
				print("Invalid axon color provided")
				axon_color = neuron["axon"].color()
		elif "dendrites_color" in kwargs:
			if check_colors(kwargs["dendrites_color"]):
				dendrites_color = kwargs["dendrites_color"]
			else: 
				print("Invalid dendrites color provided")
				dendrites_color = neuron["dendrites"].color()

		if soma_color is not None: 
			neuron["soma"].color(soma_color)
		if axon_color is not None: 
			neuron["axon"].color(axon_color)
		if dendrites_color is not None: 
			neuron["dendrites"].color(dendrites_color)


		if "mirror" in kwargs:
			if "mirror_coord" in kwargs:
				mcoord = kwargs["mirror_coord"]
			else:
				raise ValueError("Need to pass the mirror point coordinate")
			
			# mirror X positoin
			for name, actor in neuron.items():
				if "only_soma" in kwargs:
					if kwargs["only_soma"] and name != "soma": continue
					
				# get mesh points coords and shift them to other hemisphere
				if isinstance(actor, list):
					continue
				coords = actor.points()
				shifted_coords = [[c[0], c[1], mcoord + (mcoord-c[2])] for c in coords]
				actor.points(shifted_coords)
			
				neuron[name] = actor.mirror(axis='n')

	return neurons


