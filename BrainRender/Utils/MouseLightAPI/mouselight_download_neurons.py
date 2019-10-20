import sys
sys.path.append('./')

import json
import os 
from tqdm import tqdm

from BrainRender.Utils.webqueries import *


"""
	These functions take care of downloading and parsing neurons reconstrucitions from: http://ml-neuronbrowser.janelia.org/
	by sending requests to: http://ml-neuronbrowser.janelia.org/tracings/tracings. 
"""

def make_json(neuron, file_path,  axon_tracing=None, dendrite_tracing=None):
	"""[Creates a .json file that can be read by the mouselight parser.]

		Arguments:
			neuron {[dict]} -- [A dictionary with all the information about a neuron as obtained from querying http://ml-neuronbrowser.janelia.org/graphql]
			file_path {[st]} -- [path where to save the .json file]

		Keyword arguments:
			axon_tracing {[list]} -- [List of dictionaries with nodes data]
			dendrite_tracing {[list]} -- [List of dictionaries with nodes data]
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

def download_neurons(neurons_metadata):
	"""
	[Given a list of neurons metadata, as obtained by http://ml-neuronbrowser.janelia.org/graphql using BrainRender.Utils.MouseLightAPI.mouselight_info.mouselight_fetch_neurons_metadata, 
		this function downlaods tracing data from http://ml-neuronbrowser.janelia.org/tracings/tracings.]

	Arguments:
		neurons_metadata {[list]} -- [List of dictionaries with neurons metadata, used to download the tracking data and save everything to file. ]
	"""

	def get(url, tracing_id): # send a query for a single tracing ID
			query = {"ids":[tracing_id]}
			res = post_mouselight(url, query=query, clean=True)['tracings']
			return res

	print("Downloading neurons tracing data from Mouse Light")

	# variables
	fld = "Data/Morphology/MouseLight"
	url = mouselight_base_url + "tracings/tracings"

	# check arguments
	if not isinstance(neurons_metadata, list): neurons_metadata = [neurons_metadata]

	# loop over neurons
	files = []
	for neuron in tqdm(neurons_metadata):
		# Check if a .json file already exists for this neuron
		file_path = os.path.join(fld, neuron['idString']+".json")
		files.append(file_path)
		if os.path.isfile(file_path): continue

		# Get tracings by requests
		axon_tracing, dendrite_tracing = None, None
		if neuron['axon'] is not None:
			axon_tracing = get(url, neuron['axon'].id)
		if neuron['dendrite'] is not None:
			dendrite_tracing = get(url, neuron['dendrite'].id)

		# Save as  .json file: this means next time we don't have to download. Also it's necessary for the parser to render the neurons 
		make_json(neuron, file_path, axon_tracing=axon_tracing, dendrite_tracing=dendrite_tracing)
	return files
