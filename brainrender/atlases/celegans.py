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

    def __init__(self, data_folder=None, base_dir=None, **kwargs):
        Atlas.__init__(self, base_dir, **kwargs)


        # Get data
        if data_folder is None:
            raise ValueError(f"No data folder was passed, use the 'atlas_kwargs' argument of Scene to pass a data folder path")
        if not os.path.isdir(data_folder):
            raise FileNotFoundError(f"The folder {data_folder} does not exist")
        self.data_folder = data_folder

        self._get_data()


    # ----------------------------------- Utils ---------------------------------- #
    def _get_data(self):
        # Get subfolder with .obj files
        subdirs = get_subdirs(self.data_folder)
        if not subdirs:
            raise ValueError("The data folder should include a subfolder which stores the neurons .obj files")
        
        try:
            self.objs_fld = [f for f in subdirs if 'objs_smoothed' in f][0]
        except:
            raise ValueError("Could not find subdirectory with .obj files")

        self.neurons_files = [f for f in listdir(self.objs_fld) if f.lower().endswith('.obj')]
        self.neurons_names = [get_file_name(f) for f in self.neurons_files] # name of each neuron

        # Get synapses and skeleton files
        try:
            skeletons_file = [f for f in listdir(self.data_folder) if f.endswith('skeletons.json')][0]
        except:
            raise ValueError("Could not find file with neurons skeleton data")

        try:
            synapses_file = [f for f in listdir(self.data_folder) if f.endswith('synapses.csv')][0]
        except:
            raise ValueError("Could not find file with synapses data")

        # load data
        self.skeletons_data = load_json(skeletons_file)
        self.synapses_data = pd.read_csv(synapses_file, sep=';')

    def _check_neuron_argument(self, neurons):
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


    def _get_neurons(self):
        # TODO get a list of neruons (and maybe colors)
        return

    def _parse_neuron_skeleton(self, neuron):
        try: # make this work if called by a Scene class
            cs = self.atlas
        except:
            cs = self
        try:
            data = cs.skeletons_data[neuron]
        except:
            print(f'No skeleton data found for {neuron}')
            return None

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
    def add_neurons(self, neurons, alpha=1, as_skeleton=False):        
        neurons = self.atlas._check_neuron_argument(neurons)

        for neuron in neurons:
            if neuron not in self.atlas.neurons_names:
                print(f"Neuron {neuron} not included in dataset")
            else:
                color = get_random_colors() # TODO load color from metadata

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
    def add_neurons_synapses(self, neurons, pre=False, post=False):
        col_names = ['x', 'z', 'y']
        # used to correctly position synapses on .obj files

        neurons = self.atlas._check_neuron_argument(neurons)

        for neuron in neurons:
            if pre:
                data = self.atlas.synapses_data.loc[self.atlas.synapses_data.pre == neuron]
                if not len(data):
                    print(f"No pre- synapses found for neuron {neuron}")
                else:
                    data = data[['x', 'y', 'z']]
                    data['y'] = -data['y']
                    self.add_cells(data, color=self.atlas.pre_synapses_color, verbose=False,
                                        radius=self.atlas.synapses_radius, res=24, col_names = col_names)

            if post:
                rows = [i for i,row in self.atlas.synapses_data.iterrows()
                            if neuron in row.posts]
                data = self.atlas.synapses_data.iloc[rows]
                
                if not len(data):
                    print(f"No post- synapses found for neuron {neuron}")
                else:                    
                    data = data[['x', 'y', 'z']]
                    data['y'] = -data['y']
                    self.add_cells(data, color=self.atlas.post_synapses_color, verbose=False,
                        radius=self.atlas.synapses_radius, res=24, col_names = col_names)

