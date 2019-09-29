import os
import json
import pandas as pd
from collections import namedtuple


from allensdk.core.swc import read_swc

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

        


if __name__ == "__main__":
    # testing load_neuron_swc
    NEURONS_FILE = "Examples/example_files/AA0007.swc"
    load_neuron_swc(NEURONS_FILE)

