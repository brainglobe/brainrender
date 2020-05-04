import os
import json
import requests
import yaml
import gzip
import numpy as np
import scipy.io as sio
import pandas as pd
from brainio import brainio
from vtkplotter import load, Volume

# ------------------------------------ OS ------------------------------------ #
def listdir(fld):
	"""
	List the files into a folder with the coplete file path instead of the relative file path like os.listdir.

	:param fld: string, folder path

	"""
	if not os.path.isdir(fld):
		raise FileNotFoundError("Could not find directory: {}".format(fld))

	return [os.path.join(fld, f) for f in os.listdir(fld)]



def get_subdirs(folderpath):
    """
		Returns the subfolders in a given folder
	"""
    return [f.path for f in os.scandir(folderpath) if f.is_dir()]


def check_file_exists(filepath, raise_error=False):
	# Check if a file with the given path exists already
	if os.path.isfile(filepath):
		return True
	elif raise_error:
		raise FileExistsError("File {} doesn't exist".format(filepath))
	else:
		return False

def get_file_name(filepath):
    # Returns just the name, no complete path or extension
    return os.path.splitext(os.path.basename(filepath))[0]

# ------------------------------ Load/Save data ------------------------------ #
def load_npy_from_gz(filepath):
	f = gzip.GzipFile(filepath, "r")
	return np.load(f)

def save_npy_to_gz(filepath, data):
	f = gzip.GzipFile(filepath, "w")
	np.save(f, data)
	f.close()

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
	if not os.path.isfile(filepath) or not ".json" in filepath.lower(): 
		raise ValueError("unrecognized file path: {}".format(filepath))
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

def load_volume_file(filepath):
	"""
	Load a volume file (e.g., .nii) and returns the data

	:param filepath: path to file
	:param **kwargs: 

	"""
	if not os.path.isfile(filepath): raise FileNotFoundError(filepath)
	try:
		volume = brainio.load_any(filepath)
	except:
		raise ValueError(f"Could not load volume data: {filepath}")
	else:
		return volume

def load_mesh_from_file(filepath, *args, **kwargs):
	"""	
	Load a a mesh or volume from files like .obj, .stl, ...

	:param filepath: path to file
	:param **kwargs: 

	"""
	if not os.path.isfile(filepath): 
		raise FileNotFoundError(filepath)

	try:
		actor = load(filepath, *args, **kwargs)
	except:
		actor = Volume(load_volume_file(filepath, *args, **kwargs))
	
	return actor


# ----------------------------- Internet queries ----------------------------- #
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



# ----------------------------- Data manipulation ---------------------------- #
def get_probe_points_from_sharptrack(points_filepath, scale_factor=10):
	"""
		Loads the location of the of probe points as extracted by SharpTrack
		[https://github.com/cortex-lab/allenCCF].

		:param points_filepath: str, path to a .mat file with probe points
		:param scale_factor: 10, sharptrack uses a 10um reference atlas so the 
				coordinates need to be scaled to match brainrender's
	"""
	if not os.path.isfile(points_filepath) or not points_filepath.endswith(".mat"):
		raise ValueError(f"The path to the probe points .mat file is invalid: {points_filepath}")

	probe_points= sio.loadmat(points_filepath)
	probe_points =probe_points['pointList'][0][0][0][0][0]
	probe_points_df = pd.DataFrame(dict(
						x=probe_points[:,2]*scale_factor,
						y=probe_points[:,1]*scale_factor,
						z=probe_points[:,0]*scale_factor))
	return probe_points_df




