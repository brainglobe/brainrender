import sys
sys.path.append("./")

from brainrender.Utils.data_io import connected_to_internet

import requests
import time


mouselight_base_url = "http://ml-neuronbrowser.janelia.org/"


def request(url):
	"""
	Sends a request to a url

	:param url: 

	"""
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
	Sends a GET request, not currently used for anything.

	:param query: 

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

def post_mouselight(url, query=None, clean=False, attempts=3):
	"""
	sends a POST request to a user URL. Query can be either a string (in which case clean should be False) or a dictionary.

	:param url: 
	:param query: string or dictionary with query   (Default value = None)
	:param clean: if not clean, the query is assumed to be in JSON format (Default value = False)
	:param attempts: number of attempts  (Default value = 3)

	"""
	if not connected_to_internet():
		raise ConnectionError("You need an internet connection for API queries, sorry.")

	request = None
	if query is not None:
		for i in range(attempts):
			try:
				if not clean:
					time.sleep(0.01) # avoid getting an error from server
					request = requests.post(url, json={'query': query})
				else:
					time.sleep(0.01) # avoid getting an error from server
					request = requests.post(url, json=query)
			except Exception as e:
				exception = e
				request = None
				print('MouseLight API query failed. Attempt {} of {}'.format(i+1, attempts))
			if request is not None: break

		if request is None:
			raise ConnectionError("\n\nMouseLight API query failed with error message:\n{}.\
						\nPerhaps the server is down, visit 'http://ml-neuronbrowser.janelia.org' to find out.".format(exception))
	else:
		raise  NotImplementedError
	
	if request.status_code == 200:
		jreq = request.json()
		if 'data' in list(jreq.keys()):
			return jreq['data']
		else:
			return jreq
	else:
		raise Exception("Query failed to run by returning code of {}. {} -- \n\n{}".format(request.status_code, query, request.text))
