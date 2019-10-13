import os
import json
import pandas as pd
from collections import namedtuple
import requests

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

def update_folders(main_fld):
    from BrainRender.settings import folders_paths as folders_paths
    folders_paths['main_fld'] = main_fld
    folders_paths['connectivity_fld'] = os.path.join(folders_paths['main_fld'], "mouse_connectivity")                 
    folders_paths['models_fld'] = "Meshes/mouse_meshes"                                                           
    folders_paths['neurons_fld'] = os.path.join(folders_paths['main_fld'], "Mouse Light")                             
    folders_paths['save_fld'] =  os.path.join(folders_paths['main_fld'], "fc_experiments_unionized")                  
    folders_paths['rendered_scenes'] = os.path.join(folders_paths['main_fld'], "rendered_scenes")                     
    folders_paths['manifest'] = os.path.join(folders_paths['connectivity_fld'], "manifest.json")  
    folders_paths['output_fld'] = os.path.join(folders_paths['main_fld'], "output")


def listdir(fld):
    if not os.path.isdir(fld):
        raise FileNotFoundError("Could not find directory: {}".format(fld))

    return [os.path.join(fld, f) for f in os.listdir(fld)]


def load_json(filepath):
    if not os.path.isfile(filepath) or not ".json" in filepath.lower(): raise ValueError("unrecognized file path: {}".format(filepath))
    with open(filepath) as f:
        data = json.load(f)
    return data


def load_neuron_swc(filepath):
    # details on swc files: http://www.neuronland.org/NLMorphologyConverter/MorphologyFormats/SWC/Spec.html
    _sample = namedtuple("sample", "sampleN structureID x y z r parent") # sampleN structureID x y z r parent

    # in json {'allenId': 1021, 'parentNumber': 5, 'radius': 0.5, 'sampleNumber': 6, 
    # 'structureIdentifier': 2, 'x': 6848.52419500001, 'y': 2631.9816355, 'z': 3364.3552898125}
    
    if not os.path.isfile(filepath) or not ".swc" in filepath.lower(): raise ValueError("unrecognized file path: {}".format(filepath))

    f = open(filepath)
    content = f.readlines()
    f.close()

    # crate empty dicts for soma axon and dendrites
    data = {'soma':     dict(allenId=[], parentNumber=[], radius=[], sampleNumber=[], x=[], y=[], z=[]),
            'axon':     dict(allenId=[], parentNumber=[], radius=[], sampleNumber=[], x=[], y=[], z=[]),
            'dendrite':dict(allenId=[], parentNumber=[], radius=[], sampleNumber=[], x=[], y=[], z=[])}


    # start looping around samples
    for sample in content:
        if sample[0] == '#': 
            continue # skip comments
        s = _sample(*[float(samp.replace("\n", "")) for samp in sample.split("\t")])

        # what structure is this
        if s.structureID in [1., -1.]: key = "soma"
        elif s.structureID in [2.]: key = 'axon'
        elif s.structureID in [3., 4.]: key = 'dendrite'
        else:
            raise ValueError("unrecognised sample in SWC file: {}".format(s))

        # append data to dictionary
        data[key]['parentNumber'].append(int(s.parent))
        data[key]['radius'].append(s.r)
        data[key]['x'].append(s.x)
        data[key]['y'].append(s.y)
        data[key]['z'].append(s.z)
        data[key]['sampleNumber'].append(int(s.sampleN))
        data[key]['allenId'].append(-1) # TODO get allen ID from coords

    return data


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

