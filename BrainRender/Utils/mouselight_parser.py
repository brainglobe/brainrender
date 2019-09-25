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
    return neurons

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

def neurites_parser(soma_coords, neurites, neurite_radius, color, alleninfo, scene):
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
                branch_points = [soma_coords, get_coords(bp), get_coords(branch)] # this list stores all the samples that  are part of a branch
            else:
                branch_points = [get_coords(bp), get_coords(branch)] 

            # loop over all following points along the branch, until you meet either a terminal or another branching point. store the points
            idx = branch.sampleNumber
            while True:
                nxt = neurites.loc[neurites.parentNumber == idx]
                if len(nxt) != 1: 
                    break
                else:
                    branch_points.append(get_coords(nxt))
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
            region = alleninfo.loc[alleninfo.allenId == rid].acronym.values[0]
            regions.append(scene.get_structure_parent(region)['acronym'])
        except:
            pass

    return merged, regions

def neurites_parser_swc(soma_coords, neurites, neurite_radius, color, scene):
    coords = [soma_coords]
    coords.extend([get_coords(sample) for i, sample in neurites.iterrows()])
    lines = Spheres(coords, r=38, c=color, res=4)
    regions = []
    return lines, regions


def render_neuron(is_json, render_neurites,
                neurite_radius, color_neurites, axon_color, soma_color, dendrites_color, 
                random_color, neuron, neuron_number, n_neurons, scene):
        """[This function takes care of rendering a single neuron.]
        """
        # Define colors of different components
        if random_color:
            if not isinstance(random_color, str):
                color = get_random_colors(n_colors=1)
            else: # random_color is a colormap 
                color = colorMap(neuron_number, name=random_color, vmin=0, vmax=n_neurons)
            axon_color = soma_color = dendrites_color = color
        else:
            if soma_color is None:
                print("No soma color is provided, picking a random one")
                soma_color = get_random_colors(n_colors=1)

            if not color_neurites:
                axon_color = dendrites_color = soma_color
            else:
                if axon_color is None:
                    print("No axon color provided, using soma color")
                    axon_color = soma_color
                if dendrites_color is None:
                    print("No dendrites color provided, using soma color")
                    dendrites_color = soma_color

        if not check_colors([soma_color, axon_color, dendrites_color]):
            raise ValueError("The colors chosen are not valid: soma - {}, dendrites {}, axon {}".format(soma_color, dendrites_color, axon_color))

        # check if we have lists of colors
        if isinstance(soma_color, list):
            if isinstance(soma_color[0], str) or isinstance(soma_color[0], list):
                soma_color = soma_color[neuron_number]
        if isinstance(dendrites_color, list):
            if isinstance(dendrites_color[0], str) or isinstance(dendrites_color[0], list):
                dendrites_color = dendrites_color[neuron_number]
        if isinstance(axon_color, list):
            if isinstance(axon_color[0], str) or isinstance(axon_color[0], list):
                axon_color = axon_color[neuron_number]                

        # get allen info: it containes the allenID of each brain region,
        # each sample has the corresponding allen ID so we can recontruct in which brain region it is
        if 'allenInformation' in list(neuron.keys()):
            alleninfo = pd.DataFrame(neuron['allenInformation'])
            # get brain structure in which is the soma
            soma_region = scene.get_structure_parent(alleninfo.loc[alleninfo.allenId == neuron['soma']['allenId']].acronym.values[0])['acronym']
        else:
            alleninfo = None
            soma_region = scene.get_region_from_point(get_coords(neuron['soma']))
        
        if VERBOSE:
            print("Neuron {} - soma in: {}".format(neuron_number, soma_region))

        # create soma actor
        neuron_actors = {}

        soma_coords = get_coords(neuron["soma"])
        soma = Sphere(pos=soma_coords, c=soma_color, r=SOMA_RADIUS)
        neuron_actors['soma'] = soma

        # Draw dendrites and axons
        if render_neurites:
            if is_json:
                neuron_actors['dendrites'], dendrites_regions = neurites_parser(soma_coords, pd.DataFrame(neuron["dendrite"]), neurite_radius, dendrites_color, alleninfo, scene)
                neuron_actors['axon'], axon_regions = neurites_parser(soma_coords, pd.DataFrame(neuron["axon"]), neurite_radius, axon_color, alleninfo, scene)
            else:
                neuron_actors['dendrites'], dendrites_regions = neurites_parser_swc(soma_coords, pd.DataFrame(neuron["dendrite"]), neurite_radius, dendrites_color, scene)
                neuron_actors['axon'], axon_regions = neurites_parser_swc(soma_coords, pd.DataFrame(neuron["axon"]), neurite_radius, axon_color, scene)
        else:
            neuron_actors['dendrites'], dendrites_regions = [], None
            neuron_actors['axon'], axon_regions = [], None

        decimate_neuron_actors(neuron_actors)
        smooth_neurons(neuron_actors)
        return neuron_actors, {'soma':soma_region, 'dendrites':dendrites_regions, 'axon':axon_regions}

def render_neurons(ml_file, scene=None, render_neurites = True, 
                neurite_radius=None, 
                color_neurites=True, axon_color=None, soma_color=None, dendrites_color=None, random_color=False,
            ):
    
    """[Given a file with JSON data about neuronal structures downloaded from the Mouse Light neurons browser website, 
       this function creates VTKplotter actors that can be used to render the neurons, returns them as nested dictionaries]

    Arguments:
        ml_file {[string]} -- [path to the JSON MouseLight file]
        ml_file {[Scene]} -- [an instance of class Scene]
        render_neurites {[boolean]} -- [If false neurites are not rendered, just the soma]
        neurite_radius {[float]} -- [radius of the "Tube" used to render neurites, it's also used to scale the sphere used for the soma. If set to None the default is used]
        color_neurites {[Bool]} -- [default: True. If true, soma axons and dendrites are colored differently, if false each neuron has a single color (the soma color)]
        axon_color, soma_color, dendrites_color {[String, array, list]} -- [if list it needs to have the same length as the number of neurons being rendered to specify the colors for each neuron. 
                                            colors can be either strings (e.g. "red"), arrays (e.g.[.5, .5,. 5]) or variables (e.g see colors.py)]
        random_color {[Bool, str]} -- [if True each neuron will have one color picked at random among those defined in colors.py. Can also pass a string with the name of a matplotlib colormap no draw colors from that]

    Returns:
        actors [list] -- [list of dictionaries, each dictionary contains the VTK actors of one neuron]
    """
    

    """ ---------------------------------------------------------------- """

    # Check neurite radius
    if neurite_radius is None:
        neurite_radius = DEFAULT_NEURITE_RADIUS
    
    # Load the data
    if ".swc" in ml_file.lower():
        data = [load_neuron_swc(ml_file)]
        is_json = False
    else:
        is_json = True
        data = load_json(ml_file)
        data = data["neurons"]
        print("Found {} neurons".format(len(data)))

    # Partial render_neurons to set arguments
    prender_neuron = partial(render_neuron, is_json, render_neurites,
                  neurite_radius, color_neurites, axon_color, soma_color, dendrites_color, random_color)

    # Loop over neurons
    actors, regions = [], []
    if not ML_PARALLEL_PROCESSING or len(data) == 1:
        for nn, neuron in tqdm(enumerate(data)):
            neuron_actors, soma_region = prender_neuron(neuron, nn, len(data), scene)
            actors.append(neuron_actors); regions.append(soma_region)
    else:
        raise NotImplementedError("Multi core processing is not implemented yet")
    return actors, regions

def test():
    """
        Small function used to test the render_neurons function above. Specify a file path and run it
    """
    from BrainRender.scene import Scene
    res, _ = render_neurons("Examples/example_files/one_neuron.json",
                render_neurites = True,
                neurite_radius=None, 
                color_neurites=True, axon_color="red", soma_color="green", dendrites_color="blue", 
                random_color=False, scene=Scene())

    vp = Plotter(title='first example')
    for neuron in res:
        vp.show(neuron['soma'], neuron['dendrites'], neuron['axon'], interactive=True)
    

if __name__ == "__main__":
    test()