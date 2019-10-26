import os
import json
import pandas as pd
from collections import namedtuple
import requests
import yaml


from allensdk.core.swc import read_swc
from vtkplotter import *
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
import vtk

def connected_to_internet(url='http://www.google.com/', timeout=5):
	try:
		_ = requests.get(url, timeout=timeout)
		return True
	except requests.ConnectionError:
		print("No internet connection available.")
	return False

def send_query(query_string, clean=False):
	response = requests.get(query_string)
	if response.ok:
		if not clean:
			return response.json()['msg']
		else:
			return response.json()
	else:
		raise ValueError("Invalide query string: {}".format(query_string))

def listdir(fld):
	if not os.path.isdir(fld):
		raise FileNotFoundError("Could not find directory: {}".format(fld))

	return [os.path.join(fld, f) for f in os.listdir(fld)]

def strip_path(path):
    return path.strip('/').strip('\\').split('/')[-1].split('\\')

def load_json(filepath):
	if not os.path.isfile(filepath) or not ".json" in filepath.lower(): raise ValueError("unrecognized file path: {}".format(filepath))
	with open(filepath) as f:
		data = json.load(f)
	return data

def load_yaml(filepath):
	if filepath is None or not os.path.isfile(filepath): raise ValueError("unrecognized file path: {}".format(filepath))
	if not "yml" in filepath and not "yaml" in filepath: raise ValueError("unrecognized file path: {}".format(filepath))
	return yaml.load(open(filepath), Loader=yaml.FullLoader)

""" 
import allensdk.core.swc as swc

# if you ran the examples above, you will have a reconstruction here
file_name = 'cell_types/specimen_485909730/reconstruction.swc'
morphology = swc.read_swc(file_name)

# subsample the morphology 3x. root, soma, junctions, and the first child of the root are preserved.
sparse_morphology = morphology.sparsify(3)

# compartments in the order that they were specified in the file
compartment_list = sparse_morphology.compartment_list

# a dictionary of compartments indexed by compartment id
compartments_by_id = sparse_morphology.compartment_index

# the root soma compartment 
soma = morphology.soma

# all compartments are dictionaries of compartment properties
# compartments also keep track of ids of their children
for child in morphology.children_of(soma):
	print(child['x'], child['y'], child['z'], child['radius'])


"""




def load_volume_file(filepath, **kwargs):
	if not os.path.isfile(filepath): raise FileNotFoundError(filepath)

	if ".x3d" in filepath.lower(): raise ValueError("BrainRender cannot use .x3d data as they are not supported by vtkplotter")

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


if __name__ == "__main__":
	# testing load_neuron_swc
	NEURONS_FILE = "Examples/example_files/AA0007.swc"
	load_neuron_swc(NEURONS_FILE)

