
import sys
sys.path.append('./')

import os
import pandas as pd
import numpy as np
from collections import namedtuple

from vtkplotter import shapes, load, merge

from allensdk.core.cell_types_cache import CellTypesCache
from allensdk.api.queries.cell_types_api import CellTypesApi
from allensdk.core.swc import Morphology


from brainrender.Utils.paths_manager import Paths
from brainrender.Utils.data_io import connected_to_internet
from brainrender.Utils.data_manipulation import get_coords
from brainrender.scene import Scene
from brainrender.Utils.data_io import listdir


class AllenMorphology(Paths):
	""" Handles the download and visualisation of neuronal morphology data from the Allen database. """

	def __init__(self, *args, scene_kwargs={},  **kwargs):
		"""
			Initialise API interaction and fetch metadata of neurons in the Allen Database. 
		"""
		if not connected_to_internet():
			raise ConnectionError("You will need to be connected to the internet to use the AllenMorphology class")

		Paths.__init__(self, *args, **kwargs)
		self.scene = Scene(add_root=False, display_inset=False, **scene_kwargs)

		# Create a Cache for the Cell Types Cache API
		self.ctc = CellTypesCache(manifest_file=os.path.join(self.morphology_allen, 'manifest.json'))

		# Get a list of cell metadata for neurons with reconstructions, download if necessary
		self.neurons = pd.DataFrame(self.ctc.get_cells(species=[CellTypesApi.MOUSE], require_reconstruction = True))
		self.n_neurons = len(self.neurons)
		if not self.n_neurons: raise ValueError("Something went wrong and couldn't get neurons metadata from Allen")

		self.downloaded_neurons = self.get_downloaded_neurons()

	def get_downloaded_neurons(self):
		""" 
			Get's the path to files of downloaded neurons
		"""
		return [os.path.join(self.morphology_allen, f) for f in os.listdir(self.morphology_allen) if ".swc" in f]    

	def download_neurons(self, ids):
		"""
			Download neurons

		:param ids: list of integers with neurons IDs

		"""
		if isinstance(ids, np.ndarray):
			ids = list(ids)
		if not isinstance(ids, (list)): ids = [ids]

		neurons = []
		for neuron_id in ids:
			neuron_file = os.path.join(self.morphology_allen, "{}.swc".format(neuron_id))
			neurons.append(self.ctc.get_reconstruction(neuron_id, file_name=neuron_file))
		
		return neurons
		   
	def parse_neurons_swc_allen(self, morphology, color='blackboard', alpha=1):
		"""
		SWC parser for Allen neuron's morphology data, they're a bit different from the Mouse Light SWC

		:param morphology: data with morphology
		:param neuron_number: int, number of the neuron being rendered.

		"""
		# Create soma actor
		radius = 1
		neuron_actors = [shapes.Sphere(pos=get_coords(morphology.soma)[::-1], c=color, r=radius*3)]

		# loop over trees
		for tree in morphology._tree_list:
			
			tree = pd.DataFrame(tree)
			branching_points = [t.id for i,t in tree.iterrows() 
						if len(t.children)>2 and t.id < len(tree)]

			branch_starts = []
			for bp in branching_points:
				branch_starts.extend(tree.iloc[bp].children) 

			for bp in branch_starts:
				parent = tree.iloc[tree.iloc[bp].parent]
				branch = [(parent.x, parent.y, parent.z)]
				point = tree.iloc[bp]

				while True:
					branch.append((point.x, point.y, point.z))

					if not point.children:
						break
					else:
						try:
							point = tree.iloc[point.children[0]]
						except:
							break

				# Create actor
				neuron_actors.append(shapes.Tube(branch, r=radius, 
									c='red', alpha=1, res=24))

		actor = merge(*neuron_actors)
		actor.color(color)
		actor.alpha(alpha)
		return actor

	# # Todo load/save neurons??
	def load_save_neuron(self, neuron_file, neuron=None):
		neuron_name = os.path.split(neuron_file)[-1].split('.swc')[0]

		savepath = os.path.join(self.morphology_cache, neuron_name+'.vtk')

		if neuron is None and os.path.isfile(savepath):
			return load(savepath)
		elif neuron is None:
			return None
		elif neuron is not None:
			neuron.write(savepath)
	
	def parse_neuron_swc(self, filepath, color='blackboard', alpha=1,
						radius_multiplier=.1, overwrite=False):
		"""
		Given an swc file, render the neuron

		:param filepath: str with path to swc file
		:param neuron_number: numnber of neuron being rendered

		"""
		# See if we rendered this neuron already
		if not overwrite:
			loaded = self.load_save_neuron(filepath)
			if loaded is not None:
				return loaded.color(color)

		print(f"Parsing swc file: {filepath}")
		# details on swc files: http://www.neuronland.org/NLMorphologyConverter/MorphologyFormats/SWC/Spec.html
		_sample = namedtuple("sample", "sampleN structureID x y z r parent") # sampleN structureID x y z r parent
		
		if not os.path.isfile(filepath) or not ".swc" in filepath.lower(): 
			raise ValueError("unrecognized file path: {}".format(filepath))

		try:
			return self.parse_neurons_swc_allen(filepath)
		except:
			pass #  the .swc file fas not generate with by allen

		f = open(filepath)
		content = f.readlines()
		f.close()
		content = [sample.replace("\n", "") for sample in content if sample[0] != '#']
		content = [sample for sample in content if len(sample) > 3]

		# crate empty dicts for soma axon and dendrites
		data = dict(id=[], parentNumber=[], radius=[], sampleNumber=[], x=[], y=[], z=[])

		# start looping around samples
		for sample in content:
			s = _sample(*[float(samp) for samp in sample.lstrip().rstrip().split(" ")])

			# append data to dictionary
			data['id'] = s.structureID
			data['parentNumber'].append(int(s.parent))
			data['radius'].append(s.r)
			data['x'].append(s.x)
			data['y'].append(s.y)
			data['z'].append(s.z)
			data['sampleNumber'].append(int(s.sampleN))

		# Get branches and soma
		print("		reconstructing neurites trees")
		data = pd.DataFrame(data)
		radius = data['radius'].values[0] * radius_multiplier
		
		soma = data.iloc[0]
		soma = shapes.Sphere(pos=[soma.x, soma.y, soma.z], c=color, r=radius*4)
		neuron_actors = [soma]

		branches_end, branches_start = [], [] # Get branches start and end
		for parent in data.parentNumber.values:
			sons = data.loc[data.parentNumber == parent]
			if len(sons) > 1:
				branches_end.append(parent)
				for i, son in sons.iterrows():
					branches_start.append(son.sampleNumber)

		print("		creating actors")
		for start in branches_start:
			node = data.loc[data.sampleNumber == start]
			parent = data.loc[data.sampleNumber == node.parentNumber.values[0]]

			branch = [(parent.x.values[0], parent.y.values[0], parent.z.values[0])]
			while True:
				branch.append((node.x.values[0], node.y.values[0], node.z.values[0]))

				node = data.loc[data.parentNumber == node.sampleNumber.values[0]]
				if not len(node): break
				if node.sampleNumber.values[0] in branches_end: 
					branch.append((node.x.values[0], node.y.values[0], node.z.values[0]))
					break

			neuron_actors.append(shapes.Tube(branch, r=radius, 
									c='red', alpha=1, res=24))

		# Merge actors and save
		actor = merge(*neuron_actors)
		actor.color(color)
		actor.alpha(alpha)

		self.load_save_neuron(filepath, neuron=actor)
		return actor


	def add_neuron(self, neuron, shadow_axis=None, shadow_offset=-20,   
					**kwargs):
		if isinstance(neuron, list):
			neurons = neuron
		else:
			if isinstance(neuron, str):
				if os.path.isdir(neuron):
					neurons = listdir(neuron)
			else:
				neurons = [neuron]
		
		actors = []
		for neuron in neurons:
			if isinstance(neuron, str):
				neuron = self.parse_neuron_swc(neuron,  **kwargs)
			elif isinstance(neuron, Morphology):
				neuron = self.parse_neurons_swc_allen(neuron, **kwargs)

			actor = self.scene.add_vtkactor(neuron)


			# scals = actor.points()[:, 1]
			# alphas = np.linspace(0.82, .83, 250)
			# actor.pointColors(scals, alpha=alphas, cmap="Greens_r")

			# actor.points()[:, 0] += np.random.normal(0, 2000)
			# actor.points()[:, 2] += np.random.normal(0, 2000)

			if shadow_axis == 'x':
				actor.addShadow(x = shadow_offset)
			elif shadow_axis == 'y':
				actor.addShadow(y = shadow_offset)
			elif shadow_axis == 'z':
				actor.addShadow(z = shadow_offset)
			
			actors.append(neuron)




		
		return actors
		

	def render(self, **kwargs):
		self.scene.render(**kwargs)