import sys
sys.path.append('./')

import os
import json
from vtkplotter import *
import gzip

import pandas as pd
from tqdm import tqdm
import numpy as np
from tqdm import tqdm

from BrainRender.Utils.data_io import load_json
from BrainRender.Utils.data_manipulation import get_coords
from BrainRender.colors import *
from BrainRender.variables import *
from BrainRender.Utils.webqueries import request
from BrainRender.Utils.ABA.connectome import ABA


class StreamlinesAPI(ABA):
    """
        [Takes care of downloading streamliens data and other useful stuff]
    """
    base_url = "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_NNN.json.gz"

    def __init__(self):
        ABA.__init__(self) # get allen brain atlas methods

    def download_streamlines_for_region(self, region, *args, **kwargs):
        """
            [Using the Allen Mouse Connectivity data and corresponding API, this function finds expeirments whose injections
            were targeted to the region of interest and downloads the corresponding streamlines data. By default, experiements
            are selected for only WT mice and onl when the region was the primary injection target. Look at "ABA.experiments_source_search"
            to see how to change this behaviour.]

            Arguments:
                region {[str]} -- [acronym for a brain region]
        """
        # Get experiments whose injections were targeted to the region
        region_experiments = self.experiments_source_search(region, *args, **kwargs)
        try:
            return self.download_streamlines(region_experiments.id.values)
        except:
            return [], [] # <- there were no experiments in the target region 

    def download_streamlines_to_region(self, p0, *args,  mouse_line = "wt", **kwargs):
        """
            [Using the Allen Mouse Connectivity data and corresponding API, this function finds injection experiments
            which resulted in fluorescence being found in the target point, then downloads the streamlines data.]

            Arguments:
                p0 {[list, np.array]} -- [List of 3 integers defining target coordinates]

            Keyword arguments:
                mouse_line {[str, list]} -- [list of string with names to use to filter the results of the experiments search]
        """
        experiments = pd.DataFrame(self.get_projection_tracts_to_target(p0=p0))
        if mouse_line == "wt":
            experiments = experiments.loc[experiments["transgenic-line"] == ""]
        else:
            if not isinstance(mouse_line, list):
                experiments = experiments.loc[experiments["transgenic-line"] == mouse_line]
            else:
                raise NotImplementedError("ops, you've found a bug!. For now you can only pass one mouse line at the time, sorry.")
        return self.download_streamlines(experiments.id.values)


    @staticmethod
    def make_url_given_id(expid):
        return "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_{}.json.gz".format(expid)

    def extract_ids_from_csv(self, csv_file, download=False, **kwargs):
        """
            [Parse CSV file to extract experiments IDs and link to downloadable streamline data

            Given a CSV file with info about experiments downloaded from: http://connectivity.brain-map.org
            extract experiments ID and get links to download (compressed) streamline data from https://neuroinformatics.nl. 
            Also return the experiments IDs to download data from: https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html
            ]

            Arguments:
                csv_file {[str]} --  [Path to a csv file.]
        """

        try:
            data = pd.read_csv(csv_file)
        except:
            raise FileNotFoundError("Could not load: {}".format(csv_file))
        else:
            if not download:
                print("Found {} experiments.\n".format(len(data.id.values)))

        if not download: 
            print("To download compressed data, click on the following URLs:")
            for eid in data.id.values:
                url = self.make_url_given_id(eid)
                print(url)

            print("\n")
            string = ""
            for x in data.id.values:
                string += "{},".format(x)

            print("To download JSON directly, go to: https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html")
            print("and  copy and paste the following experiments ID in the 'Enter the Allen Connectivity Experiment number:' field.")
            print("You can copy and paste each individually or a list of IDs separated by a comma")
            print("IDs: {}".format(string[:-1]))
            print("\n")

            return data.id.values
        else:
            return self.download_streamlines(data.id.values, **kwargs)

    def download_streamlines(self, eids, streamlines_folder=None):
        """
            [Given a list of expeirmental IDs, it downloads the streamline data from the https://neuroinformatics.nl cache and saves them as 
            json files. ]

            Arguments:
                eids {[list, np.array, tuple]} -- [list of experiments IDs (either integers or strings)]
                streamlines_folder {[str]} -- [path to folder in which to store the streamlines data, if None the default is used.]
        """
        if streamlines_folder is None:
            streamlines_folder = self.streamlines_cache

        if not isinstance(eids, (list, np.ndarray, tuple)): eids = [eids]

        filepaths, data = [], []
        for eid in tqdm(eids):
            url = self.make_url_given_id(eid)
            jsonpath = os.path.join(streamlines_folder, str(eid)+".json")
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



def parse_streamline(*args, filepath=None, data=None, show_injection_site=True, color='ivory', alpha=.8, radius=10, **kwargs):
    """
        [Given a path to a .json file with streamline data (or the data themselves), render the streamline as tubes actors.]

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
        data = {k:{int(k2):v2 for k2, v2 in v.items()} for k,v in data.items()}
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
        lines.append(shapes.Tube(points,  r=radius, c=color, alpha=alpha, res=STREAMLINES_RESOLUTION))

    coords = []
    if show_injection_site:
        if len(data['injection_sites']) == 1:
            injection_data = data['injection_sites'][0]
        else:
            injection_data = data['injection_sites']

        for inj in injection_data:
            coords.append(list(inj.values()))
        spheres = [shapes.Spheres(coords, r=INJECTION_VOLUME_SIZE)]
    else:
        spheres = []

    merged = merge(*lines, *spheres)
    merged.color(color)
    merged.alpha(alpha)
    return [merged]










