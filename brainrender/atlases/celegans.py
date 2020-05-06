"""
This class rendereds datasets of the whole C. Elegans connectome. 
All data from Daniel Witvliet (https://www.biorxiv.org/content/10.1101/2020.04.30.066209v1)
"""

import pandas as pd
import numpy as np
import os
from tqdm import tqdm
from PIL import ImageColor

from vtkplotter import load, merge, save
from vtkplotter.shapes import Tube

from brainrender.atlases.base import Atlas
from brainrender.Utils.webqueries import request
from brainrender.Utils.data_io import load_mesh_from_file, listdir, get_subdirs, load_json, get_file_name
from brainrender.colors import get_random_colors
from brainrender import NEURON_RESOLUTION




class Celegans(Atlas):

    atlas_name = "Celegans"
    mesh_format = 'obj' # or obj, stl etc..

    pre_synapses_color = 'salmon'
    post_synapses_color = 'skyblue'
    synapses_radius = .125

    skeleton_radius = .05


    default_camera = dict(
        position = [-15.686, 65.978, 32.901] ,
        focal = [13.312, 20.159, -9.482],
        viewup = [-0.896, -0.412, -0.168],
        distance = 68.823,
        clipping = [26.154, 122.7] ,
    )

    def __init__(self, data_folder=None, base_dir=None, **kwargs):
        """
            This class handles loading and parsing neuroanatomical data for the C. elegans connectome from 
            https://www.biorxiv.org/content/10.1101/2020.04.30.066209v1

            :param base_dir: path to directory to use for saving data (default value None)
            :param kwargs: can be used to pass path to individual data folders. See brainrender/Utils/paths_manager.py
            :param data_folder: str, path to a folder with data for the connectome # TODO replace with downloading data
        """
        # Initialise atlas
        Atlas.__init__(self, base_dir, **kwargs)

        # Get data
        if data_folder is None:
            raise ValueError(f"No data folder was passed, use the 'atlas_kwargs' argument of Scene to pass a data folder path")
        if not os.path.isdir(data_folder):
            raise FileNotFoundError(f"The folder {data_folder} does not exist")
        self.data_folder = data_folder
        self._get_data()

    # ----------------------------------- Utils ---------------------------------- #
    def get_neurons_by(self, getby='pair', lookup=None):
        """
            Selects a subset of the neurons using some criteria and lookup key, 
            based on the neurons metadata

            :param getby: str, name of the metadata key to use for selecting neurons
            :param lookup: str/int.. neurons whose attribute 'getby' matches the lookup value will be selected

            :returns: list of strings with neurons names
        """
        try: # make this work if called by a Scene class
            cs = self.atlas
        except:
            cs = self

        allowed = ['neuron', 'pair', 'class', 'type']

        if getby not in allowed:
            raise ValueError(f'Get by key should be one of {allowed} not {getby}')

        filtered = list(cs.neurons_metadata.loc[cs.neurons_metadata[getby] == lookup]['neuron'].values)
        if not filtered:
            print(f"Found 0 neurons with getby {getby} and lookup {lookup}")

        return filtered

    def get_neuron_color(self, neuron, colorby='type'):
        """
            Get a neuron's RGB color. Colors can be assigned based on different criteria
            like the neuron's type or by individual neuron etc...

            :param neuron: str, nueron name
            :param colorby: str, metadata attribute to use for coloring
            :returns: rgb values of color
        """
        try: # make this work if called by a Scene class
            cs = self.atlas
        except:
            cs = self

        allowed = ['neuron', 'individual', 'ind', 'pair', 'class', 'type']

        if colorby not in allowed:
            raise ValueError(f"color by key should be one of {allowed} not {colorby}")

        if colorby == 'type':
            color = cs.neurons_metadata.loc[cs.neurons_metadata.neuron == neuron]['type_color'].values[0]
            color = ImageColor.getrgb(color)
        elif colorby == 'individual' or colorby == 'ind' or colorby == 'neuron':
            color = get_random_colors()
        else:
            raise NotImplementedError

        return color

    def _get_data(self):
        """
            Loads data and metadata for the C. elegans connectome.
        """
        # Get subfolder with .obj files
        subdirs = get_subdirs(self.data_folder)
        if not subdirs:
            raise ValueError("The data folder should include a subfolder which stores the neurons .obj files")
        
        try:
            self.objs_fld = [f for f in subdirs if 'objs_smoothed' in f][0]
        except:
            raise FileNotFoundError("Could not find subdirectory with .obj files")

        # Get filepath to each .obj 
        self.neurons_files = [f for f in listdir(self.objs_fld) if f.lower().endswith('.obj')]

        # Get synapses and skeleton files
        try:
            skeletons_file = [f for f in listdir(self.data_folder) if f.endswith('skeletons.json')][0]
        except:
            raise FileNotFoundError("Could not find file with neurons skeleton data")

        try:
            synapses_file = [f for f in listdir(self.data_folder) if f.endswith('synapses.csv')][0]
        except:
            raise FileNotFoundError("Could not find file with synapses data")

        # load data
        self.skeletons_data = load_json(skeletons_file)
        self.synapses_data = pd.read_csv(synapses_file, sep=';')

        # Get neurons metadata
        try:
            metadata_file = [f for f in listdir(self.data_folder) if 'neuron_metadata.csv' in f][0]
        except:
            raise FileNotFoundError(f'Could not find neurons metadata file {metadata_file}')

        self.neurons_metadata = pd.read_csv(metadata_file)
        self.neurons_names = list(self.neurons_metadata.neuron.values)

    def _check_neuron_argument(self, neurons):
        """
            Checks if a list of string includes neurons name, returns only
            elements of the list that are correct names

            :param neurons: list of strings with neurons names
        """
        try: # make this work if called by a Scene class
            cs = self.atlas
        except:
            cs = self

        if not isinstance(neurons, (list, tuple)):
            neurons = [neurons]

        good_neurons = []
        for neuron in neurons:
            if neuron not in cs.neurons_names:
                print(f"Neuron {neuron} not in dataset")
            else:
                good_neurons.append(neuron)
        return good_neurons

    def _parse_neuron_skeleton(self, neuron):
        """
            Parses a neuron's skeleton information from skeleton .json file
            to create a vtk actor that represents the neuron

            :param neuron: str, neuron name
        """
        try: # make this work if called by a Scene class
            cs = self.atlas
        except:
            cs = self
        try:
            data = cs.skeletons_data[neuron]
        except:
            print(f'No skeleton data found for {neuron}')
            return None

        # Create an actor for each neuron's branch and then merge
        actors = []
        for branch in data['branches']:
            coords = [data['coordinates'][str(p)] for p in branch]

            # Just like for synapses we need to adjust the coordinates to match the .obj files
            # coords are x z -y
            adjusted_coords = [(c[0], c[2], -c[1]) for c in coords]
            actors.append(Tube(adjusted_coords, r=cs.skeleton_radius, res=NEURON_RESOLUTION))

        return merge(*actors)


    # ------------------------------- Atlas methods ------------------------------ #
    @staticmethod # static method because it inherits from scene
    def add_neurons(self, neurons, alpha=1, as_skeleton=False, colorby='type'):   
        """
            THIS METHODS GETS CALLED BY SCENE, self referes to the instance of Scene not to this class.
            Renders neurons and adds them to the scene. 

            :param neurons: list of names of neurons
            :param alpha: float in range 0,1 -  neurons transparency
            :param as_skeleton: bool (Default value = False), if True neurons are rendered as skeletons 
                                otherwise as a full mesh showing the whole morphology
            :param colorby: str, criteria to use to color the neurons. Accepts values like type, individual etc. 
        """
        neurons = self.atlas._check_neuron_argument(neurons)

        for neuron in neurons:
            if neuron not in self.atlas.neurons_names:
                print(f"Neuron {neuron} not included in dataset")
            else:
                color = self.atlas.get_neuron_color(neuron, colorby=colorby)

                if as_skeleton: # reconstruct skeleton from json
                    neuron = self.atlas._parse_neuron_skeleton(neuron)
                    if neuron is None: 
                        continue
                    else:
                        neuron.color(color)

                else: # load as .obj file
                    try:
                        neuron_file = [f for f in self.atlas.neurons_files if neuron in f][0]
                    except:
                        print(f"Could not find .obj file for neuron {neuron}")
                        continue

                    neuron = load_mesh_from_file(neuron_file, c=color)

                # Refine actor's look
                neuron.alpha(alpha)

                # Add to scene
                self.actors['neurons'].append(neuron)


    @staticmethod
    def add_neurons_synapses(self, neurons, alpha=1, pre=False, post=False, colorby='synapse_type'):
        """
            THIS METHODS GETS CALLED BY SCENE, self referes to the instance of Scene not to this class.
            Renders neurons and adds them to the scene. 

            :param neurons: list of names of neurons
            :param alpha: float in range 0,1 -  neurons transparency
            :param pre: bool, if True the presynaptic sites of each neuron are rendered
            :param post: bool, if True the postsynaptic sites on each neuron are rendered
            :param colorby: str, criteria to use to color the neurons.
                             Accepts values like synapse_type, type, individual etc. 
        """
        col_names = ['x', 'z', 'y']
        # used to correctly position synapses on .obj files

        neurons = self.atlas._check_neuron_argument(neurons)

        for neuron in neurons:
            if pre:
                if colorby == 'synapse_type':
                    color = self.atlas.pre_synapses_color
                else:
                    color = self.atlas.get_neuron_color(neuron, colorby=colorby)

                data = self.atlas.synapses_data.loc[self.atlas.synapses_data.pre == neuron]
                if not len(data):
                    print(f"No pre- synapses found for neuron {neuron}")
                else:
                    data = data[['x', 'y', 'z']]
                    data['y'] = -data['y']
                    self.add_cells(data, color=color, verbose=False, alpha=alpha,
                                        radius=self.atlas.synapses_radius, res=24, col_names = col_names)

            if post:
                if colorby == 'synapse_type':
                    color = self.atlas.post_synapses_color
                else:
                    color = self.atlas.get_neuron_color(neuron, colorby=colorby)

                rows = [i for i,row in self.atlas.synapses_data.iterrows()
                            if neuron in row.posts]
                data = self.atlas.synapses_data.iloc[rows]
                
                if not len(data):
                    print(f"No post- synapses found for neuron {neuron}")
                else:                    
                    data = data[['x', 'y', 'z']]
                    data['y'] = -data['y']
                    self.add_cells(data, color=color, verbose=False, alpha=alpha,
                        radius=self.atlas.synapses_radius, res=24, col_names = col_names)

