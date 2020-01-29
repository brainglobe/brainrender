import os
import json
import requests
import yaml

def connected_to_internet(url='http://www.google.com/', timeout=5):
	"""
		Check that there is an internet connection

		:param url: url to use for testing (Default value = 'http://www.google.com/')
		:param timeout:  timeout to wait for [in seconds] (Default value = 5)
	"""
	
	try:
		_ = requests.get(url, timeout=timeout)
		return True
	except requests.ConnectionError:
		print("No internet connection available.")
	return False

def send_query(query_string, clean=False):
	"""
	Send a query/request to a website

	:param query_string: string with query content
	:param clean:  (Default value = False)

	"""
	response = requests.get(query_string)
	if response.ok:
		if not clean:
			return response.json()['msg']
		else:
			return response.json()
	else:
		raise ValueError("Invalide query string: {}".format(query_string))

def listdir(fld):
	"""
	List the files into a folder with the coplete file path instead of the relative file path like os.listdir.

	:param fld: string, folder path

	"""
	if not os.path.isdir(fld):
		raise FileNotFoundError("Could not find directory: {}".format(fld))

	return [os.path.join(fld, f) for f in os.listdir(fld)]

def save_json(filepath, content, append=False):
	"""
	Saves content to a JSON file

	:param filepath: path to a file (must include .json)
	:param content: dictionary of stuff to save

	"""
	if not 'json' in filepath:
		raise ValueError("filepath is invalid")

	if not append:
		with open(filepath, 'w') as json_file:
			json.dump(content, json_file, indent=4)
	else:
		with open(filepath, 'w+') as json_file:
			json.dump(content, json_file, indent=4)


def save_yaml(filepath, content, append=False, topcomment=None):
	"""
	Saves content to a yaml file

	:param filepath: path to a file (must include .yaml)
	:param content: dictionary of stuff to save

	"""
	if not 'yaml' in filepath:
		raise ValueError("filepath is invalid")

	if not append:
		method = 'w'
	else:
		method = 'w+'

	with open(filepath, method) as yaml_file:
		if topcomment is not None:
			yaml_file.write(topcomment)
		yaml.dump(content,yaml_file, default_flow_style=False, indent=4)

def load_json(filepath):
	"""
	Load a JSON file

	:param filepath: path to a file

	"""
	if not os.path.isfile(filepath) or not ".json" in filepath.lower(): raise ValueError("unrecognized file path: {}".format(filepath))
	with open(filepath) as f:
		data = json.load(f)
	return data

def load_yaml(filepath):
	"""
	Load a YAML file

	:param filepath: path to yaml file

	"""
	if filepath is None or not os.path.isfile(filepath): raise ValueError("unrecognized file path: {}".format(filepath))
	if not "yml" in filepath and not "yaml" in filepath: raise ValueError("unrecognized file path: {}".format(filepath))
	return yaml.load(open(filepath), Loader=yaml.FullLoader)


def load_volume_file(filepath, **kwargs):
	"""
	Load a volume file (e.g., .nii) and return vtk actor

	:param filepath: path to file
	:param **kwargs: 

	"""
	from vtkplotter import Volume, load
	if not os.path.isfile(filepath): raise FileNotFoundError(filepath)

	if ".x3d" in filepath.lower(): raise ValueError("brainrender cannot use .x3d data as they are not supported by vtkplotter")

	elif "nii" in filepath.lower() or ".label" in filepath.lower():
		import nibabel as nb
		data = nb.load(filepath)
		d = data.get_fdata()

		act = Volume(d, **kwargs)

	else:
		act = load(filepath, **kwargs)
		if act is None:
			raise ValueError("Could not load {}".format(filepath))

	return act

