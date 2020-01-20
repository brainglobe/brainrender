import sys
sys.path.append('./')

import json
import os 
from tqdm import tqdm

from brainrender.Utils.webqueries import post_mouselight, mouselight_base_url
from brainrender.Utils.paths_manager import Paths


"""
	These functions take care of downloading and parsing neurons reconstrucitions from: http://ml-neuronbrowser.janelia.org/
	by sending requests to: http://ml-neuronbrowser.janelia.org/tracings/tracings. 
"""
class MouseLightAPI(Paths):
	def __init__(self, base_dir=None, **kwargs):
		"""
			Handles the download of neurons morphology data from the Mouse Light project

			:param base_dir: path to directory to use for saving data (default value None)
			:param kwargs: can be used to pass path to individual data folders. See brainrender/Utils/paths_manager.py
		"""
		Paths.__init__(self, base_dir=base_dir, **kwargs)

	@staticmethod
	def make_json(neuron, file_path,  axon_tracing=None, dendrite_tracing=None):
		"""
		Creates a .json file with the neuron's data that can be read by the mouselight parser.

		:param neuron: dict with neuron's data
		:param file_path: str, path where to save the json file
		:param axon_tracing: list with data for axon tracing (Default value = None)
		:param dendrite_tracing: list with data for dendrite tracing (Default value = None)

		"""
		# parse axon
		if axon_tracing is not None:
			nodes = axon_tracing[0]['nodes']
			axon = [
				dict(
					sampleNumber = n['sampleNumber'],
					x = n['x'],
					y = n['y'],
					z = n['z'],
					radius = n['radius'],
					parentNumber = n['parentNumber'],
				)
				for n in nodes]
		else:
			axon = []

		# parse dendrites
		if dendrite_tracing is not None:
			nodes = dendrite_tracing[0]['nodes']
			dendrite = [
				dict(
					sampleNumber = n['sampleNumber'],
					x = n['x'],
					y = n['y'],
					z = n['z'],
					radius = n['radius'],
					parentNumber = n['parentNumber'],
				)
				for n in nodes]
		else:
			dendrite = []

		content = dict(
			neurons = [
				dict(
					idString = neuron['idString'],
					soma = dict(
						x = neuron['soma'].x,
						y = neuron['soma'].y,
						z = neuron['soma'].z,
					),
					axon = axon, 
					dendrite = dendrite,

				)
			]
		)

		# save to file
		with open(file_path, 'w') as f:
			json.dump(content, f)


	def download_neurons(self, neurons_metadata):
		"""
		Given a list of neurons metadata, as obtained by interaction with the mouselight databse [http://ml-neuronbrowser.janelia.org/graphql]
		using brainrender.Utils.MouseLightAPI.mouselight_info.mouselight_fetch_neurons_metadata,
		this function downlaods tracing data from http://ml-neuronbrowser.janelia.org/tracings/tracings.]

		:param neurons_metadata: list with metadata for neurons to download

		"""

		def get(url, tracing_id): # send a query for a single tracing ID
			"""
			Creates the URL for each neuron to download

			:param url: str with url
			:param tracing_id: str with the neuron's ID

			"""
			query = {"ids":[tracing_id]}
			res = post_mouselight(url, query=query, clean=True)['tracings']
			return res

		if neurons_metadata is None or not neurons_metadata:
			return None
		print("Downloading neurons tracing data from Mouse Light")

		# check arguments
		if not isinstance(neurons_metadata, list): neurons_metadata = [neurons_metadata]


		# URL used to fetch neurons
		url = mouselight_base_url + "tracings/tracings"

		# loop over neurons
		files = []
		for neuron in tqdm(neurons_metadata):
			# Check if a .json file already exists for this neuron
			file_path = os.path.join(self.morphology_mouselight, neuron['idString']+".json")
			files.append(file_path)
			if os.path.isfile(file_path): continue

			# Get tracings by requests
			axon_tracing, dendrite_tracing = None, None
			if neuron['axon'] is not None:
				axon_tracing = get(url, neuron['axon'].id)
			if neuron['dendrite'] is not None:
				dendrite_tracing = get(url, neuron['dendrite'].id)

			# Save as  .json file: this means next time we don't have to download. Also it's necessary for the parser to render the neurons 
			self.make_json(neuron, file_path, axon_tracing=axon_tracing, dendrite_tracing=dendrite_tracing)
		return files
