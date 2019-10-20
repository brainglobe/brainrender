import sys
sys.path.append("./")

from BrainRender.Utils.data_io import connected_to_internet

import requests
import json
import urllib.request as urlreq
import urllib.error as urlerr


mouselight_base_url = "http://ml-neuronbrowser.janelia.org/"

def query_mouselight(query):
	if not connected_to_internet():
		raise ConnectionError("You need an internet connection for API queries, sorry.")
	
	base_url = "http://ml-neuronbrowser.janelia.org/"

	full_query = base_url + query

	# send the query, package the return argument as a json tree
	response = requests.get(full_query)
	if response.ok:
		json_tree = response.json()
		if json_tree['success']:
			return json_tree
		else:
			exception_string = 'did not complete api query successfully'
	else:
		exception_string = 'API failure. Allen says: {}'.format(
			response.reason)

	# raise an exception if the API request failed
	raise ValueError(exception_string)

def post_mouselight(url, query=None):
	if not connected_to_internet():
		raise ConnectionError("You need an internet connection for API queries, sorry.")

	if query is not None:
			request = requests.post(url, json={'query': query})
	else:
		raise  NotImplementedError
	
	if request.status_code == 200:
		return request.json()['data']
	else:
		raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
