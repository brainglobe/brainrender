import sys
sys.path.append('./')

import pandas as pd
from collections import namedtuple

from BrainRender.Utils.webqueries import *

def mouselight_api_info():
	# Get infos from the ML API
	url = mouselight_base_url + "graphql"
	# query =  "systemSettings {apiVersion apiRelease neuronCount\}}"
	query =  \
			"""
			query {
				queryData {
					totalCount
					}
				}
			"""
	res =  post_mouselight(url, query=query)
	print("{} neurons on MouseLight database. ".format(res['queryData']['totalCount']))

def mouselight_get_brainregions():
	# Download metadata about brain regions from the ML API
	url = mouselight_base_url + "graphql"
	# query =  "systemSettings {apiVersion apiRelease neuronCount\}}"
	query =  \
			"""
			query {
				brainAreas{
					
					acronym
					name
					id
					atlasId
					graphOrder
					parentStructureId
					structureIdPath
				}
			}
			"""
	res =  post_mouselight(url, query=query)['brainAreas']

	keys = {k:[] for k in res[0].keys()}
	for r in res:
		for k in r.keys():
			keys[k].append(r[k])
	
	structures_data = pd.DataFrame.from_dict(keys)
	return structures_data


def mouselight_structures_identifiers():
	# Download the identifiers used in ML neurons tracers
	url = mouselight_base_url + "graphql"
	# query =  "systemSettings {apiVersion apiRelease neuronCount\}}"
	query =  \
		"""
			query {
				structureIdentifiers{
					id
					name
					value
				}
			}
		"""
	res =  post_mouselight(url, query=query)['structureIdentifiers']

	keys = {k:[] for k in res[0].keys()}
	for r in res:
		for k in r.keys():
			keys[k].append(r[k])
	
	structures_identifiers = pd.DataFrame.from_dict(keys)
	return structures_identifiers

def mouselight_fetch_neurons_metadata():
	print("Querying MouseLight API...")
	url = mouselight_base_url + "graphql"
	query = """
 			query {
				searchNeurons{
				queryTime
				totalCount
				
				neurons{
				tag
				id
				idNumber
				idString
				  
				brainArea{
					acronym
				}

				  
				tracings{
					soma{
					x
					y
					z
					radius
					brainArea{
						id
					  	acronym
					}
					sampleNumber
					parentNumber
					
					}
				  
				  id
				  tracingStructure{
					name
					value
					id
				  }
				}
				}
			}
			}
			"""

	res =  post_mouselight(url, query=query)['searchNeurons']
	print("     ... fetched metadata for {} neurons in {}s".format(res["totalCount"], round(res["queryTime"]/1000, 2)))

	# Process neurons
	neurons = res['neurons']
	node = namedtuple("node", "x y z r area_acronym sample_n parent_n")
	tracing_structure = namedtuple("tracing_structure", "id name value named_id")

	cleaned_nurons = []
	for neuron in neurons:
		if neuron['brainArea'] is not None:
			brainArea_acronym = neuron['brainArea']['acronym'],
		else:
			brainArea_acronym = None,

		if len(neuron['tracings']) > 1:
			dendrite = tracing_structure(
				neuron['tracings'][1]['id'],
				neuron['tracings'][1]['tracingStructure']['name'],
				neuron['tracings'][1]['tracingStructure']['value'],
				neuron['tracings'][1]['tracingStructure']['id'],
			)
		else:
			dendrite = None


		clean_neuron = dict(
			brainArea_acronym = brainArea_acronym,
			id = neuron['id'],
			idNumber = neuron['idNumber'],
			idString = neuron['idString'],
			tag=neuron['tag'],
			soma = node(
				neuron['tracings'][0]['soma']['x'],
				neuron['tracings'][0]['soma']['y'],
				neuron['tracings'][0]['soma']['z'],
				neuron['tracings'][0]['soma']['radius'],
				neuron['tracings'][0]['soma']['brainArea'],
				neuron['tracings'][0]['soma']['sampleNumber'],
				neuron['tracings'][0]['soma']['parentNumber']
			),
			axon = tracing_structure(
				neuron['tracings'][0]['id'],
				neuron['tracings'][0]['tracingStructure']['name'],
				neuron['tracings'][0]['tracingStructure']['value'],
				neuron['tracings'][0]['tracingStructure']['id'],
			),
			dendrite = dendrite,
		)
		cleaned_nurons.append(clean_neuron)


	# TODO filter neurons by search criteria

	neurons_ids = [n['id'] for n in cleaned_nurons]

	return neurons_ids, cleaned_nurons
