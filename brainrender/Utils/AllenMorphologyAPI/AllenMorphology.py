
import sys
sys.path.append('./')

import os
import pandas as pd
import numpy as np
from collections import namedtuple

from vtkplotter import shapes, load, merge

from allensdk.core.cell_types_cache import CellTypesCache
from allensdk.api.queries.cell_types_api import CellTypesApi

from brainrender.Utils.paths_manager import Paths
from brainrender.Utils.data_io import connected_to_internet
from brainrender.Utils.data_manipulation import get_coords

"""
	WORK IN PROGRESS

	This class should handle the download and visualisation of neuronal morphology data from the Allen database.
"""


class AllenMorphology(Paths):
	""" Handles the download and visualisation of neuronal morphology data from the Allen database. """

	def __init__(self, *args, **kwargs):
		"""
			Initialise API interaction and fetch metadata of neurons in the Allen Database. 
		"""
		if not connected_to_internet():
			raise ConnectionError("You will need to be connected to the internet to use the AllenMorphology class")

		Paths.__init__(self, *args, **kwargs)

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
		   
	def parse_neurons_swc_allen(self, morphology, color=None):
		"""
		SWC parser for Allen neuron's morphology data, they're a bit different from the Mouse Light SWC

		:param morphology: data with morphology
		:param neuron_number: int, number of the neuron being rendered.

		"""
		# Create soma actor
		neuron_actors = [shapes.Sphere(pos=get_coords(morphology.soma)[::-1], c=color, r=4)]

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
				neuron_actors.append(shapes.Tube(branch, r=2, 
									c='red', alpha=1, res=24))

		actor = merge(*neuron_actors)
		actor.color(color)
		return actor

	def load_save_neuron(self, neuron_file):
		neuron_name = os.path.split(neuron_file)[-1].split('.swc')[0]

		savepath = os.path.join(self.morphology_cache, neuron_name+'.vtk')

		if 
	
	def parse_neuron_swc(self, filepath, color='darkseagreen'):
		"""
		Given an swc file, render the neuron

		:param filepath: str with path to swc file
		:param neuron_number: numnber of neuron being rendered

		"""
		# details on swc files: http://www.neuronland.org/NLMorphologyConverter/MorphologyFormats/SWC/Spec.html
		_sample = namedtuple("sample", "sampleN structureID x y z r parent") # sampleN structureID x y z r parent

		# in json {'allenId': 1021, 'parentNumber': 5, 'radius': 0.5, 'sampleNumber': 6, 
		# 'structureIdentifier': 2, 'x': 6848.52419500001, 'y': 2631.9816355, 'z': 3364.3552898125}
		
		if not os.path.isfile(filepath) or not ".swc" in filepath.lower(): 
			raise ValueError("unrecognized file path: {}".format(filepath))

		try:
			morphology = allen_swc.read_swc(filepath)
			return self.parse_neurons_swc_allen(morphology)
		except:
			pass #  the .swc file fas not generate with by allen

		f = open(filepath)
		content = f.readlines()
		f.close()
		content = [sample for sample in content if sample[0] != '#' and len(sample) > 3]

		# crate empty dicts for soma axon and dendrites
		data = dict(id=[], parentNumber=[], radius=[], sampleNumber=[], x=[], y=[], z=[])

		# start looping around samples
		for sample in content:
			s = _sample(*[float(samp.replace("\n", "")) for samp in sample.split(" ")])

			# append data to dictionary
			data['id'] = s.structureID
			data['parentNumber'].append(int(s.parent))
			data['radius'].append(s.r)
			data['x'].append(s.x)
			data['y'].append(s.y)
			data['z'].append(s.z)
			data['sampleNumber'].append(int(s.sampleN))

		# Get branches and soma
		data = pd.DataFrame(data)
		radius = data['radius'].values[0]
		soma = data.iloc[0]
		soma = shapes.Sphere(pos=[soma.x, soma.y, soma.z], c=color, r=radius*2)
		neuron_actors = [soma]

		branches_end, branches_start = [], [] # Get branches start and end
		for parent in data.parentNumber.values:
			sons = data.loc[data.parentNumber == parent]
			if len(sons) > 1:
				branches_end.append(parent)
				for i, son in sons.iterrows():
					branches_start.append(son.sampleNumber)

		neuron_actors = [] # Create an actor for each branch
		for start in branches_start:
			node = data.loc[data.sampleNumber == start]
			parent = data.loc[data.sampleNumber == node.parentNumber.values[0]]

			branch = [(parent.x.values[0], parent.y.values[0], parent.x.values[0])]
			while True:
				branch.append((node.x.values[0], node.y.values[0], node.x.values[0]))

				node = data.loc[data.parentNumber == node.sampleNumber.values[0]]
				if not len(node): break
				if node.sampleNumber.values[0] in branches_end: 
					break

			neuron_actors.append(shapes.Tube(branch, r=radius, 
									c='red', alpha=1, res=24))

		actor = merge(*neuron_actors)
		actor.color(color)
		return actor



if __name__ == '__main__':
	AM = AllenMorphology()
	AM.download_neurons(AM.neurons.id.values[:10])
