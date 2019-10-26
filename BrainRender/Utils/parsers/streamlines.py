import sys
sys.path.append('./')

import os
import json
from vtkplotter import *
import gzip

import pandas as pd
from tqdm import tqdm
import numpy as np

from BrainRender.Utils.data_io import load_json
from BrainRender.Utils.data_manipulation import get_coords
from BrainRender.colors import *
from BrainRender.variables import *
from BrainRender.Utils.webqueries import request

def download_streamlines(urls, streamlines_folder="Data/Streamlines"):
    if not isinstance(urls, list): urls = [urls]
    filepaths, data = [], []
    for url in urls:
        exp_id = url.split(".json")[0].split("_")[-1]
        jsonpath = os.path.join(streamlines_folder, exp_id+".json")
        filepaths.append(jsonpath)
        if not os.path.isfile(jsonpath):
            response = request(url)

            # Write the response content as a temporary compressed file
            temp_path = os.path.join(streamlines_folder, "temp.gz")
            with open(temp_path, "wb") as temp:
                temp.write(response.content)

            # Open in pandas and delete temp
            url_data = pd.read_json(temp_path, lines=True, compression='gzip')
            os.remove(temp_path)

            # save json
            url_data.to_json(jsonpath)

            # append to lists and return
            data.append(url_data)
        else:
            data.append(pd.read_json(jsonpath))
    return filepaths, data


def extract_ids_from_csv(csv_file, download=False, **kwargs):
    """
        [Parse CSV file to extract experiments IDs and link to downloadable streamline data

        Given a CSV file with info about experiments downloaded from: http://connectivity.brain-map.org
        extract experiments ID and get links to download (compressed) streamline data from https://neuroinformatics.nl. 
        Also return the experiments IDs to download data from: https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html
        ]

        Arguments:
            csv_file {[str]} --  [Path to a csv file.]
    """
    #  url_model =  https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_480074702.json.gz.
    try:
        data = pd.read_csv(csv_file)
    except:
        raise FileNotFoundError("Could not load: {}".format(csv_file))
    else:
        print("Found {} experiments.\n".format(len(data.id.values)))

    if not download: print("To download compressed data, click on the following URLs:")
    urls = []
    for eid in data.id.values:
        url = "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_{}.json.gz".format(eid)
        if not download: print(url)
        urls.append(url)

    if not download: 
        print("\n")
        string = ""
        for x in data.id.values:
            string += "{},".format(x)

        print("To download JSON directly, go to: https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html")
        print("and  copy and paste the following experiments ID in the 'Enter the Allen Connectivity Experiment number:' field.")
        print("You can copy and paste each individually or a list of IDs separated by a comma")
        print("IDs: {}".format(string[:-1]))
        print("\n")

    if not download:
        return data.id.values, urls
    else:
        return download_streamlines(urls, **kwargs)

def parse_streamline(*args, filepath=None, data=None, show_injection_site=True, color='ivory', alpha=.8, radius=10, **kwargs):
    """
        [Given a path to a .json file with streamline data, render the streamline as tubes actors.]

        Arguments:
            filepath {[str, list]} -- [Either a path to a .json file or a list of file paths]
            data {[pd.DataFrame, list]} -- [Either a dataframe or a list of dataframes with streamlines data]

        Keyword arguments:
            color {[str, color]} -- [Color of the streamlines actors]
            alpha {[float]} -- [range 0,1  transparency of the streamlines]
            radius {[int]} -- [radius of the tubes used to render the streamlines]
            show_injection_site {[bool]} -- [If true a sphere is rendered at the coordinates for the injection site]
    """
    if filepath is not None and data is None:
        data = load_json(filepath)
    elif filepath is None and data is not None:
        pass
    else:
        raise ValueError("Need to pass eiteher a filepath or data argument to parse_streamline")

    # create actors for streamlines
    lines = []
    if len(data['lines']) == 1:
        lines_data = data['lines'][0]
    else:
        lines_data = data['lines']
    for line in lines_data:
        points = [[l['x'], l['y'], l['z']] for l in line]
        lines.append(shapes.Tube(points,  r=radius, c=color, alpha=alpha, res=NEURON_RESOLUTION))

    # TODO add injections rendering

    merged = merge(*lines)
    merged.color(color)
    return [merged]










