import sys
sys.path.append('./')

import pandas as pd
from collections import namedtuple

from BrainRender.Utils.webqueries import *
from BrainRender.Utils.ABA.connectome import ABA
from BrainRender.Utils.data_manipulation import is_any_item_in_list


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

def mouselight_fetch_neurons_metadata(filterby = None, filter_regions=None):
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
					id
					acronym
					name
					safeName
					atlasId
					aliases
					structureIdPath
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
			brainArea_acronym = neuron['brainArea']['acronym']
			brainArea_id = neuron['brainArea']['id']
			brainArea_name = neuron['brainArea']['name']
			brainArea_safename = neuron['brainArea']['safeName']
			brainArea_atlasId = neuron['brainArea']['atlasId']
			brainArea_aliases = neuron['brainArea']['aliases']
			brainArea_structureIdPath = neuron['brainArea']['structureIdPath']
		else:
			brainArea_acronym = None
			brainArea_id = None
			brainArea_name = None
			brainArea_safename = None
			brainArea_atlasId = None
			brainArea_aliases = None
			brainArea_structureIdPath = None

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
			brainArea_id = brainArea_id,
			brainArea_name = brainArea_name,
			brainArea_safename = brainArea_safename,
			brainArea_atlasId = brainArea_atlasId,
			brainArea_aliases = brainArea_aliases,
			brainArea_structureIdPath = brainArea_structureIdPath,

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

	if filterby is not None:
		if filter_regions is None:
			raise ValueError("If filtering neuron by region, you need to pass a list of filter regions to use")

		# Get structure tree 
		aba = ABA()
		ancestors_tree = aba.structure_tree.get_ancestor_id_map()
		filter_regions_ids = [struct['id'] for struct in aba.structure_tree.get_structures_by_acronym(filter_regions)]

		if filterby == "soma":
			filtered_neurons = []
			for neuron in cleaned_nurons:
				if neuron['brainArea_acronym'] is None: 
					continue
				region = aba.structure_tree.get_structures_by_acronym([neuron['brainArea_acronym']])[0]
				region_ancestors = ancestors_tree[region['id']]
				if is_any_item_in_list(filter_regions_ids, region_ancestors):
					filtered_neurons.append(neuron)


			print("	... selected {} neurons out of {}".format(len(filtered_neurons), res["totalCount"]))
			return filtered_neurons
		else:
			raise NotImplementedError("Filter neurons by {} is not implemented".format(filterby))
	else:
		return cleaned_nurons
