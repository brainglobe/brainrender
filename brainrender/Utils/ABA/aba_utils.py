import os
import pandas as pd
import numpy as np

from tqdm import tqdm

from vtkplotter import ProgressBar, shapes, merge, load

import brainrender
from brainrender.Utils.data_io import load_mesh_from_file, load_json
from brainrender.Utils.webqueries import request


""" 
    Code to support atlases.aba.ABA
"""



def experiments_source_search(mca, SOI, *args, source=True,  **kwargs):
        """
        Returns data about experiments whose injection was in the SOI, structure of interest
        :param SOI: str, structure of interest. Acronym of structure to use as seed for teh search
        :param *args: 
        :param source:  (Default value = True)
        :param **kwargs: 
        """
        """
            list of possible kwargs
                injection_structures : list of integers or strings
                    Integer Structure.id or String Structure.acronym.
                target_domain : list of integers or strings, optional
                    Integer Structure.id or String Structure.acronym.
                injection_hemisphere : string, optional
                    'right' or 'left', Defaults to both hemispheres.
                target_hemisphere : string, optional
                    'right' or 'left', Defaults to both hemispheres.
                transgenic_lines : list of integers or strings, optional
                    Integer TransgenicLine.id or String TransgenicLine.name. Specify ID 0 to exclude all TransgenicLines.
                injection_domain : list of integers or strings, optional
                    Integer Structure.id or String Structure.acronym.
                primary_structure_only : boolean, optional
                product_ids : list of integers, optional
                    Integer Product.id
                start_row : integer, optional
                    For paging purposes. Defaults to 0.
                num_rows : integer, optional
                    For paging purposes. Defaults to 2000.
        """
        transgenic_id = kwargs.pop('transgenic_id', 0) # id = 0 means use only wild type
        primary_structure_only = kwargs.pop('primary_structure_only', True)

        if not isinstance(SOI, list): SOI = [SOI]

        if source:
            injection_structures=SOI
            target_domain = None
        else:
            injection_structures = None
            target_domain = SOI

        return pd.DataFrame(mca.experiment_source_search(injection_structures=injection_structures,
                                            target_domain = target_domain,
                                            transgenic_lines=transgenic_id,
                                            primary_structure_only=primary_structure_only))


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
        lines.append(shapes.Tube(points,  r=radius, c=color, alpha=alpha, res=brainrender.STREAMLINES_RESOLUTION))

    coords = []
    if show_injection_site:
        if len(data['injection_sites']) == 1:
            injection_data = data['injection_sites'][0]
        else:
            injection_data = data['injection_sites']

        for inj in injection_data:
            coords.append(list(inj.values()))
        spheres = [shapes.Spheres(coords, r=brainrender.INJECTION_VOLUME_SIZE)]
    else:
        spheres = []

    merged = merge(*lines, *spheres)
    merged.color(color)
    merged.alpha(alpha)
    return [merged]


def make_url_given_id(expid):
    """
        Get url of JSON file for an experiment, give it's ID number

        :param expid: int with experiment ID number

    """
    return "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_{}.json.gz".format(expid)


def download_streamlines(eids, streamlines_folder=None):
    """
        Given a list of expeirmental IDs, it downloads the streamline data from the https://neuroinformatics.nl cache and saves them as
        json files. 

        :param eids: list of integers with experiments IDs
        :param streamlines_folder: str path to the folder where the JSON files should be saved, if None the default is used (Default value = None)

    """

    if not isinstance(eids, (list, np.ndarray, tuple)): eids = [eids]

    filepaths, data = [], []
    for eid in tqdm(eids):
        url = make_url_given_id(eid)
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


def extract_ids_from_csv(csv_file, download=False, **kwargs):
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
            url = make_url_given_id(eid)
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
        return download_streamlines(data.id.values, **kwargs)

