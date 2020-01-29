import sys
sys.path.append('./')

import os
from vtkplotter import shapes, merge

import pandas as pd
from tqdm import tqdm
import numpy as np

from brainrender.Utils.data_io import load_json
from brainrender import STREAMLINES_RESOLUTION, INJECTION_VOLUME_SIZE
from brainrender.Utils.webqueries import request
from brainrender.Utils.ABA.connectome import ABA


class StreamlinesAPI(ABA):
    """
        Takes care of downloading streamlines data and other useful stuff
    """
    base_url = "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_NNN.json.gz"

    def __init__(self):
        ABA.__init__(self) # get allen brain atlas methods

    def download_streamlines_for_region(self, region, *args, **kwargs):
        """
            Using the Allen Mouse Connectivity data and corresponding API, this function finds expeirments whose injections
            were targeted to the region of interest and downloads the corresponding streamlines data. By default, experiements
            are selected for only WT mice and onl when the region was the primary injection target. Look at "ABA.experiments_source_search"
            to see how to change this behaviour.

            :param region: str with region to use for research
            :param *args: arguments for ABA.experiments_source_search
            :param **kwargs: arguments for ABA.experiments_source_search

        """
        # Get experiments whose injections were targeted to the region
        region_experiments = self.experiments_source_search(region, *args, **kwargs)
        try:
            return self.download_streamlines(region_experiments.id.values)
        except:
            return [], [] # <- there were no experiments in the target region 

    def download_streamlines_to_region(self, p0, *args,  mouse_line = "wt", **kwargs):
        """
            Using the Allen Mouse Connectivity data and corresponding API, this function finds injection experiments
            which resulted in fluorescence being found in the target point, then downloads the streamlines data.

            :param p0: list of floats with XYZ coordinates
            :param mouse_line: str with name of the mouse line to use(Default value = "wt")
            :param *args: 
            :param **kwargs: 

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
        """
            Get url of JSON file for an experiment, give it's ID number

            :param expid: int with experiment ID number

        """
        return "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_{}.json.gz".format(expid)


    def extract_ids_from_csv(self, csv_file, download=False, **kwargs):
        """
            Parse CSV file to extract experiments IDs and link to downloadable streamline data
        
            Given a CSV file with info about experiments downloaded from: http://connectivity.brain-map.org
            extract experiments ID and get links to download (compressed) streamline data from https://neuroinformatics.nl.
            Also return the experiments IDs to download data from: https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html
            

            :param csv_file: str with path to csv file
            :param download: if True the data are downloaded automatically (Default value = False)
            :param **kwargs: 

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
            Given a list of expeirmental IDs, it downloads the streamline data from the https://neuroinformatics.nl cache and saves them as
            json files. 

            :param eids: list of integers with experiments IDs
            :param streamlines_folder: str path to the folder where the JSON files should be saved, if None the default is used (Default value = None)

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
        Given a path to a .json file with streamline data (or the data themselves), render the streamline as tubes actors.
        Either  filepath or data should be passed

        :param filepath: str, optional. Path to .json file with streamline data (Default value = None)
        :param data: panadas.DataFrame, optional. DataFrame with streamline data. (Default value = None)
        :param color: str color of the streamlines (Default value = 'ivory')
        :param alpha: float transparency of the streamlines (Default value = .8)
        :param radius: int radius of the streamlines actor (Default value = 10)
        :param show_injection_site: bool, if True spheres are used to render the injection volume (Default value = True)
        :param *args: 
        :param **kwargs: 

    """
    if filepath is not None and data is None:
        data = load_json(filepath)
        # data = {k:{int(k2):v2 for k2, v2 in v.items()} for k,v in data.items()}
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










