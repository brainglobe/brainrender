import sys
sys.path.append('./')

import os
import json
from vtkplotter import *

import pandas as pd
from tqdm import tqdm
import numpy as np

from BrainRender.Utils.data_io import load_json, load_neuron_swc
from BrainRender.Utils.data_manipulation import get_coords
from BrainRender.colors import *
from BrainRender.variables import *

# https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html


def extract_ids_from_csv(csv_file):
    """
        Given a CSV file with info about experiments downloaded from: http://connectivity.brain-map.org
        extract experiments ID and get links to download (compressed) streamline data. 
        Also return the experiments IDs to download data from: https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html
    """
    #  url_model =  https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_480074702.json.gz.
    try:
        data = pd.read_csv(csv_file)
    except:
        raise FileNotFoundError("Could not load: {}".format(csv_file))
    else:
        print("Found {} experiments.\n".format(len(data.id.values)))

    print("To download compressed data, click on the following URLs:")
    for eid in data.id.values:
        print("https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_{}.json.gz".format(eid))
    print("\n")
    string = ""
    for x in data.id.values:
        string += "{},".format(x)

    print("To download JSON directly, go to: https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html")
    print("Then, copy and paste the following experiments ID in the 'Enter the Allen Connectivity Experiment number:' field.")
    print("You can copy and paste each individually or a list of IDs separated by a comma")
    print("IDs: {}".format(string[:-1]))
    print("\n")
    return data.id.values

def parse_streamline(filepath, *args, color='ivory', alpha=.8, radius=6, **kwargs):
    """
        Given a path to a .json file with streamline data, render the streamline as tubes actors
    """
    data = load_json(filepath)

    # create actors for streamlines
    lines = []
    for line in data['lines']:
        points = [[l['x'], l['y'], l['z']] for l in line]
        lines.append(shapes.Tube(points,  r=radius, c=color, alpha=alpha, res=NEURON_RESOLUTION))

    merged = merge(*lines)
    merged.color(color)
    return [merged]


def test():
    streamliens_file = "Examples\example_files\streamlines.json"
    
    from BrainRender.scene import Scene
    scene = Scene()
    scene.add_streamlines(streamliens_file, color='turquoise') 
    scene.add_brain_regions(['VAL'], colors='ivory', alpha=.4)
    
    scene.render()




if __name__ == "__main__":
    test()










