import sys
sys.path.append('./')

import os
import json
from vtkplotter import *

import pandas as pd
from tqdm import tqdm
import numpy as np
# import multiprocessing as mp
# from pathos.multiprocessing import ProcessingPool as Pool
from functools import partial

from BrainRender.Utils.data_io import load_json, load_neuron_swc
from BrainRender.Utils.data_manipulation import get_coords
from BrainRender.colors import *
from BrainRender.variables import *

import multiprocessing as mp

# import ray
# ray.init(ignore_reinit_error=True)

class NeuronsParser:
    def __init__(self, scene=None, 
                render_neurites = True, mirror=False, 
                neurite_radius=None, color_by_region=False, force_to_hemisphere=None,
                color_neurites=True, axon_color=None, soma_color=None, dendrites_color=None, random_color=False):
        self.scene = scene # for the meaning of the arguments check self.render_neurons
        self.render_neurites = render_neurites 
        self.neurite_radius = neurite_radius 
        self.color_neurites = color_neurites 
        self.axon_color = axon_color 
        self.soma_color = soma_color 
        self.dendrites_color = dendrites_color 
        self.random_color = random_color
        self.mirror = mirror
        self.color_by_region = color_by_region
        self.force_to_hemisphere = force_to_hemisphere

    def render_neurons(self, ml_file, **kwargs):
        """[Given a file with JSON data about neuronal structures downloaded from the Mouse Light neurons browser website, 
            this function creates VTKplotter actors that can be used to render the neurons, returns them as nested dictionaries]

        Arguments:
            ml_file {[string]} -- [path to the JSON MouseLight file]
            scene {[Scene]} -- [an instance of class Scene]
            render_neurites {[boolean]} -- [If false neurites are not rendered, just the soma]
            neurite_radius {[float]} -- [radius of the "Tube" used to render neurites, it's also used to scale the sphere used for the soma. If set to None the default is used]
            color_neurites {[Bool]} -- [default: True. If true, soma axons and dendrites are colored differently, if false each neuron has a single color (the soma color)]
            mirror {[Bool]} -- [default: False. mirror neuron on the horizontal axis]
            axon_color, soma_color, dendrites_color {[String, array, list]} -- [if list it needs to have the same length as the number of neurons being rendered to specify the colors for each neuron. 
                                                colors can be either strings (e.g. "red"), arrays (e.g.[.5, .5,. 5]) or variables (e.g see colors.py)]
            random_color {[Bool, str]} -- [if True each neuron will have one color picked at random among those defined in colors.py. Can also pass a string with the name of a matplotlib colormap no draw colors from that]
            color_by_region {[bool]} -- [If true neurons are colored by the allen atlas' color of the region the soma is in]
            force_to_hemisphere {[str]} -- [Can have values: 'left', 'right' and None. If not none it makes sure that all neurons have some in that hemisphere by mirroring those that dont]

        Returns:
            actors [list] -- [list of dictionaries, each dictionary contains the VTK actors of one neuron]
        """

        # parse options
        if "scene" in list(kwargs.keys()):
            self.scene = kwargs['scene']
        if "render_neurites" in list(kwargs.keys()):
            self.render_neurites = kwargs['render_neurites']
        if "neurite_radius" in list(kwargs.keys()):
            self.neurite_radius = kwargs['neurite_radius']
        if "color_neurites" in list(kwargs.keys()):
            self.color_neurites = kwargs['color_neurites']
        if "axon_color" in list(kwargs.keys()):
            self.axon_color = kwargs['axon_color']
        if "soma_color" in list(kwargs.keys()):
            self.soma_color = kwargs['soma_color']
        if "dendrites_color" in list(kwargs.keys()):
            self.dendrites_color = kwargs['dendrites_color']
        if "random_color" in list(kwargs.keys()):
            self.random_color = kwargs['random_color']
        if "mirror" in list(kwargs.keys()):
            self.mirror = kwargs['mirror']
        if "force_to_hemisphere" in list(kwargs.keys()):
            self.force_to_hemisphere = kwargs['force_to_hemisphere']
        if 'color_by_region' in list(kwargs.keys()):
            self.color_by_region = kwargs['color_by_region']

        # if mirror. get mirror coordinates
        if self.mirror:
            self.mirror_coord = self.scene.get_region_CenterOfMass('root', unilateral=False)[2]
        else:
            self.mirror_coord = False
        self.mirror_ax = 'x'

        # Check neurite radius
        if self.neurite_radius is None:
            neurite_radius = DEFAULT_NEURITE_RADIUS
        
        # Load the data
        if ".swc" in ml_file.lower():
            data = [load_neuron_swc(ml_file)]
            self.is_json = False
        else:
            self.is_json = True
            data = load_json(ml_file)
            data = data["neurons"]
            print("Found {} neurons".format(len(data)))

        # Render neurons
        self.n_neurons  = len(data)
        actors, regions = [], []
        if not ML_PARALLEL_PROCESSING or self.n_neurons == 1: # parallel processing
            # Loop over neurons
            for nn, neuron in tqdm(enumerate(data)):
                neuron_actors, soma_region = self.render_neuron(neuron, nn)
                actors.append(neuron_actors); regions.append(soma_region)
        else:
            raise NotImplementedError("Multi core processing is not implemented yet")
            # n_cores =  mp.cpu_count()
            # print("Number of processors: ", n_cores)

            # futures = []
            # for nn, neuron in enumerate(data):
            #     arguments = args.copy()
            #     arguments.extend([neuron, nn])
            #     futures.append(prender_neuron.remote(*arguments))

            # print(ray.get(futures))

        return actors, regions

    def render_neuron(self, neuron, neuron_number):
        """[This function takes care of rendering a single neuron.]
        """
        # Define colors of different components
        if not self.color_by_region:
            if self.random_color:
                if not isinstance(self.random_color, str):
                    color = get_random_colors(n_colors=1)
                else: # random_color is a colormap 
                    color = colorMap(neuron_number, name=self.random_color, vmin=0, vmax=self.n_neurons)
                axon_color = soma_color = dendrites_color = color
            else:
                if self.soma_color is None:
                    print("No soma color is provided, picking a random one")
                    soma_color = get_random_colors(n_colors=1)

                if not self.color_neurites:
                    axon_color = dendrites_color = soma_color = self.soma_color
                else:
                    soma_color = self.soma_color
                    if self.axon_color is None:
                        print("No axon color provided, using soma color")
                        axon_color = soma_color
                    else:
                        axon_color = self.axon_color
                    if self.dendrites_color is None:
                        print("No dendrites color provided, using soma color")
                        dendrites_color = soma_color
                    else:
                        dendrites_color = self.dendrites_color

            # check that the colors make sense
            if not check_colors([soma_color, axon_color, dendrites_color]):
                raise ValueError("The colors chosen are not valid: soma - {}, dendrites {}, axon {}".format(soma_color, dendrites_color, axon_color))

            # check if we have lists of colors or single colors
            if isinstance(soma_color, list):
                if isinstance(soma_color[0], str) or isinstance(soma_color[0], list):
                    soma_color = soma_color[neuron_number]
            if isinstance(dendrites_color, list):
                if isinstance(dendrites_color[0], str) or isinstance(dendrites_color[0], list):
                    dendrites_color = dendrites_color[neuron_number]
            if isinstance(axon_color, list):
                if isinstance(axon_color[0], str) or isinstance(axon_color[0], list):
                    axon_color = axon_color[neuron_number]                

        # get allen info: it containes the allenID of each brain region
        # each sample has the corresponding allen ID so we can recontruct in which brain region it is
        if 'allenInformation' in list(neuron.keys()):
            self.alleninfo = pd.DataFrame(neuron['allenInformation'])             # get brain structure in which is the soma
            soma_region = self.scene.get_structure_parent(self.alleninfo.loc[self.alleninfo.allenId == neuron['soma']['allenId']].acronym.values[0])['acronym']
        else:
            self.alleninfo = None
            soma_region = self.scene.get_region_from_point(get_coords(neuron['soma']))

        soma_region = self.scene.get_structure_parent(soma_region)['acronym']

        if self.color_by_region:
            try:
                region_color = self.scene.structure_tree.get_structures_by_acronym([soma_region])[0]['rgb_triplet']
            except:
                print("could not find default color for region: {}. Using random color instead".format(soma_region))
                region_color = get_random_colors(n_colors=1)

            axon_color = soma_color = dendrites_color = region_color

        if VERBOSE:
            print("Neuron {} - soma in: {}".format(neuron_number, soma_region))

        # create soma actor
        neuron_actors = {}

        self.soma_coords = get_coords(neuron["soma"], mirror=self.mirror_coord, mirror_ax=self.mirror_ax)
        neuron_actors['soma'] = Sphere(pos=self.soma_coords, c=soma_color, r=SOMA_RADIUS)

        # Draw dendrites and axons
        if self.render_neurites:
            if self.is_json:
                neuron_actors['dendrites'], dendrites_regions = self.neurites_parser(pd.DataFrame(neuron["dendrite"]), dendrites_color)
                neuron_actors['axon'], axon_regions = self.neurites_parser(pd.DataFrame(neuron["axon"]), axon_color)
            else:
                neuron_actors['dendrites'], dendrites_regions = self.neurites_parser_swc(pd.DataFrame(neuron["dendrite"]), dendrites_color)
                neuron_actors['axon'], axon_regions = self.neurites_parser_swc(pd.DataFrame(neuron["axon"]), axon_color)
        else:
            neuron_actors['dendrites'], dendrites_regions = [], None
            neuron_actors['axon'], axon_regions = [], None

        self.decimate_neuron_actors(neuron_actors)
        self.smooth_neurons(neuron_actors)

        # force to hemisphere
        if self.force_to_hemisphere is not None:
            mirror_coor = self.scene.get_region_CenterOfMass('root', unilateral=False)[2]

            if self.force_to_hemisphere.lower() == "left":
                if self.soma_coords[2] > mirror_coor:
                    neuron_actors = self.mirror_neuron(neuron_actors, mirror_coor)
            elif self.force_to_hemisphere.lower() == "right":
                if self.soma_coords[2] < mirror_coor:
                    neuron_actors = self.mirror_neuron(neuron_actors, mirror_coor)
            else:
                raise ValueError("unrecognised argument for force to hemisphere: {}".format(self.force_to_hemisphere))


        return neuron_actors, {'soma':soma_region, 'dendrites':dendrites_regions, 'axon':axon_regions}

    @staticmethod
    def decimate_neuron_actors(neuron_actors):
        """
            Can be used to decimate the VTK actors for the neurons (i.e. reduce number of polygons). Should make the rendering faster
        """
        if DECIMATE_NEURONS:
            for k, actors in neuron_actors.items():
                if not isinstance(actors, list):
                    actors.decimate()
                else:
                    for actor in actors:
                        actor.decimate() 

    @staticmethod
    def smooth_neurons(neuron_actors):
        """
            Can be used to smooth the VTK actors for the neurons. Should improve apect of neurons
        """
        if SMOOTH_NEURONS:
            for k, actors in neuron_actors.items():
                if not isinstance(actors, list):
                    actors.smoothLaplacian()
                else:
                    for actor in actors:
                        actor.smoothLaplacian()

    def neurites_parser(self, neurites, color):
        """[Given a dataframe with all the samples for some neurites, create "Tube" actors that render each neurite segment.]
        
        Arguments:
            neurites {[DataFrame]} -- [dataframe with each sample for the neurites]
            neurite_radius {[float]} -- [radius of the Tube actors]
            color {[color object]} -- [color to be assigned to the Tube actor]
            alleninfo {Data frame]} -- [dataframe with Info about brain regions from Allen]


        Returns:
            actors {[list]} -- [list of VTK actors]

        ----------------------------------------------------------------
        This function works by first identifyingt the branching points of a neurite structure. Then each segment between either two branchin points
        or between a branching point and a terminal is modelled as a Tube. This minimizes the number of actors needed to represent the neurites
        while stil accurately modelling the neuron. 

        Known issue: the axon initial segment is missing from renderings. 
        """
        if self.neurite_radius is None:
            neurite_radius = DEFAULT_NEURITE_RADIUS
        else:
            neurite_radius = self.neurite_radius

        # get branching points
        try:
            parent_counts = neurites["parentNumber"].value_counts()
        except:
            if len(neurites) == 0:
                print("Couldn't find neurites data")
                return [], []
            else:
                raise ValueError("Something went wrong while rendering neurites:\n{}".format(neurites))
        branching_points = parent_counts.loc[parent_counts > 1]

        # loop over each branching point
        actors = []
        for idx, bp in branching_points.iteritems():
            # get neurites after the branching point
            bp = neurites.loc[neurites.sampleNumber == idx]
            post_bp = neurites.loc[neurites.parentNumber == idx]
            
            # loop on each branch after the branching point
            for bi, branch in post_bp.iterrows():
                if bi == 0:
                    branch_points = [self.soma_coords, get_coords(bp, mirror=self.mirror_coord, mirror_ax=self.mirror_ax), get_coords(branch, mirror=self.mirror_coord, mirror_ax=self.mirror_ax)] # this list stores all the samples that  are part of a branch
                else:
                    branch_points = [get_coords(bp, mirror=self.mirror_coord, mirror_ax=self.mirror_ax), get_coords(branch, mirror=self.mirror_coord, mirror_ax=self.mirror_ax)] 

                # loop over all following points along the branch, until you meet either a terminal or another branching point. store the points
                idx = branch.sampleNumber
                while True:
                    nxt = neurites.loc[neurites.parentNumber == idx]
                    if len(nxt) != 1: 
                        break
                    else:
                        branch_points.append(get_coords(nxt, mirror=self.mirror_coord, mirror_ax=self.mirror_ax))
                        idx += 1

                # if the branch is too short for a tube, create a sphere instead
                if len(branch_points) < 2: # plot either a line between two branch_points or  a spheere
                    actors.append(Sphere(branch_points[0], c="g", r=100))
                    continue 
                
                # create tube actor
                actors.append(shapes.Tube(branch_points, r=neurite_radius, c=color, alpha=1, res=NEURON_RESOLUTION))
        
        # merge actors' meshes to make rendering faster
        merged = merge(*actors)
        merged.color(color)

        # get regions the neurites go through
        regions = []
        for rid in set(neurites.allenId.values):
            try:
                region = self.alleninfo.loc[self.alleninfo.allenId == rid].acronym.values[0]
                regions.append(self.scene.get_structure_parent(region)['acronym'])
            except:
                pass

        return merged, regions

    def neurites_parser_swc(self, neurites, color):
        coords = [self.soma_coords]
        coords.extend([get_coords(sample, mirror=self.mirror_coord, mirror_ax=self.mirror_ax) for i, sample in neurites.iterrows()])
        lines = Spheres(coords, r=38, c=color, res=4)
        regions = []
        return lines, regions

    def mirror_neuron(self, neuron, mcoord):
        for name, actor in neuron.items():
            # get mesh points coords and shift them to other hemisphere
            if isinstance(actor, (list, tuple, str)) or actor is None:
                continue
            coords = actor.coordinates()
            shifted_coords = [[c[0], c[1], mcoord + (mcoord-c[2])] for c in coords]
            actor.setPoints(shifted_coords)
        
            neuron[name] = actor.mirror(axis='n')
        return neuron

    def filter_neurons_by_region(self, neurons, regions, neurons_regions=None):
        """[Only returns neurons whose soma is in one of the regions in regions]
        
        Arguments:
            neurons {[type]} -- [description]
            regions {[type]} -- [description]
        """

        if not isinstance(neurons, list): neurons = [neurons]
        if not isinstance(regions, list): regions = [regions]
        if neurons_regions is not None:
            if not isinstance(neurons_regions, list):
                neurons_regions = [neurons_regions]

        keep = []
        for i, neuron in enumerate(neurons):
            if neurons_regions is None:
                try:
                    coords = neuron['soma'].centerOfMass()
                except: raise ValueError(neuron)
                region = self.scene.get_region_from_point(coords)
            else:
                if isinstance(neurons_regions[0], dict):
                    region = neurons_regions[i]['soma']
                else:
                    region = neurons_regions[i]

            if region is None: 
                continue
            elif region in regions:
                keep.append(neuron)
            else:
                continue

        return keep


def edit_neurons(neurons, **kwargs):
    """
        Modify neurons actors after they have been created, at render time. 
        neurons should be a list of dictionaries with soma, dendrite and axon actors of each neuron.
    """
    soma_color, axon_color, dendrites_color = None, None, None
    for neuron in neurons:
        if "random_color" in kwargs:
            if kwargs["random_color"]:
                if not isinstance(kwargs["random_color"], str):
                    color = get_random_colors(n_colors=1)
                else: # random_color is a colormap 
                    color = colorMap(np.random.randint(1000), name=kwargs["random_color"], vmin=0, vmax=1000)
                axon_color = soma_color = dendrites_color = color
        elif "color_neurites" in kwargs:
            soma_color = neuron["soma"].color()
            if not kwargs["color_neurites"]:
                axon_color = dendrites_color = soma_color
            else:
                if not "axon_color" in kwargs:
                    print("no axon color provided, using somacolor")
                    axon_color = soma_color
                else:
                    axon_color = kwargs["axon_color"]

                if not "dendrites_color" in kwargs:
                    print("no dendrites color provided, using somacolor")
                    dendrites_color = soma_color
                else:
                    dendrites_color = kwargs["dendrites_color"]
        elif "soma_color" in kwargs:
            if check_colors(kwargs["soma_color"]):
                soma_color = kwargs["soma_color"]
            else: 
                print("Invalid soma color provided")
                soma_color = neuron["soma"].color()
        elif "axon_color" in kwargs:
            if check_colors(kwargs["axon_color"]):
                axon_color = kwargs["axon_color"]
            else: 
                print("Invalid axon color provided")
                axon_color = neuron["axon"].color()
        elif "dendrites_color" in kwargs:
            if check_colors(kwargs["dendrites_color"]):
                dendrites_color = kwargs["dendrites_color"]
            else: 
                print("Invalid dendrites color provided")
                dendrites_color = neuron["dendrites"].color()

        if soma_color is not None: 
            neuron["soma"].color(soma_color)
        if axon_color is not None: 
            neuron["axon"].color(axon_color)
        if dendrites_color is not None: 
            neuron["dendrites"].color(dendrites_color)


        if "mirror" in kwargs:
            if "mirror_coord" in kwargs:
                mcoord = kwargs["mirror_coord"]
            else:
                raise ValueError("Need to pass the mirror point coordinate")
            
            # mirror X positoin
            for name, actor in neuron.items():
                if "only_soma" in kwargs:
                    if kwargs["only_soma"] and name != "soma": continue
                    
                # get mesh points coords and shift them to other hemisphere
                if isinstance(actor, list):
                    continue
                coords = actor.coordinates()
                shifted_coords = [[c[0], c[1], mcoord + (mcoord-c[2])] for c in coords]
                actor.setPoints(shifted_coords)
            
                neuron[name] = actor.mirror(axis='n')

    return neurons



def test():
    """
        Small function used to test the render_neurons function above. Specify a file path and run it
    """
    from BrainRender.scene import Scene
    np = NeuronsParser(render_neurites = True,
                neurite_radius=None, 
                color_neurites=True, axon_color="red", soma_color="green", dendrites_color="blue", 
                random_color=False, scene=Scene())
    res, _ = np.render_neurons("Examples/example_files/one_neuron.json")

    vp = Plotter(title='first example')
    for neuron in res:
        vp.show(neuron['soma'], neuron['dendrites'], neuron['axon'], interactive=True)
    

if __name__ == "__main__":
    test()