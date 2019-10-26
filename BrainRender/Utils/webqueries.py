import sys
sys.path.append("./")

from BrainRender.Utils.data_io import connected_to_internet

import requests
import json
import urllib.request as urlreq
import urllib.error as urlerr


mouselight_base_url = "http://ml-neuronbrowser.janelia.org/"


def request(url):
	if not connected_to_internet():
		raise ConnectionError("You need to have an internet connection to send requests.")
	response = requests.get(url)
	if response.ok:
		return response
	else:
		exception_string = 'URL request failed: {}'.format(response.reason)
	raise ValueError(exception_string)

def query_mouselight(query):
	"""
		[Sends a GET request, not currently used for anything.]
	"""
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

def post_mouselight(url, query=None, clean=False):
	"""
		[sends a POST request to a user URL. Query can be either a string (in which case clean should be False) or a dictionary.]
	"""
	if not connected_to_internet():
		raise ConnectionError("You need an internet connection for API queries, sorry.")

	if query is not None:
		if not clean:
			request = requests.post(url, json={'query': query})
		else:
			request = requests.post(url, json=query)
	else:
		raise  NotImplementedError
	
	if request.status_code == 200:
		jreq = request.json()
		if 'data' in list(jreq.keys()):
			return jreq['data']
		else:
			return jreq
	else:
		raise Exception("Query failed to run by returning code of {}. {}".format(request.status_code, query))
