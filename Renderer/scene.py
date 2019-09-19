import sys
sys.path.append('./')   # <- necessary to import packages from other directories within the project

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from collections import namedtuple
from vtkplotter import Plotter, show, interactive, Video, settings, Sphere, shapes

from Utils.data_io import load_json
from Utils.data_manipulation import get_coords
from colors import *
from variables import *
from Renderer.brain_render import BrainRender
from settings import *

"""
    The code below aims to create a scene to which actors can be added or removed, changed etc..
    It also facilitates the interaction with the scene (e.g. moving the camera) and the creation of 
    snapshots or animated videos. 
    The class Scene is based on the Plotter class of Vtkplotter: https://github.com/marcomusy/vtkplotter/blob/master/vtkplotter/plotter.py
    and other classes within the same package. 
"""

# TODO add a way to keep track of which actor is which [e.g. a dict with names for the differen actors etc],
# probs a wrapper around add actors


class Scene(BrainRender):  # subclass brain render to have acces to structure trees
    VIP_regions = DEFAULT_VIP_REGIONS
    VIP_color = DEFAULT_VIP_COLOR

    interactive_commands = """
 ==========================================================
| Press: i     print info about selected object            |
|        m     minimise opacity of selected mesh           |
|        .,    reduce/increase opacity                     |
|        /     maximize opacity                            |
|        w/s   toggle wireframe/solid style                |
|        p/P   change point size of vertices               |
|        l     toggle edges line visibility                |
|        x     toggle mesh visibility                      |
|        X     invoke a cutter widget tool                 |
|        1-3   change mesh color                           |
|        4     use scalars as colors, if present           |
|        5     change background color                     |
|        0-9   (on keypad) change axes style               |
|        k     cycle available lighting styles             |
|        K     cycle available shading styles              |
|        o/O   add/remove light to scene and rotate it     |
|        n     show surface mesh normals                   |
|        a     toggle interaction to Actor Mode            |
|        j     toggle interaction to Joystick Mode         |
|        r     reset camera position                       |
|        C     print current camera info                   |
|        S     save a screenshot                           |
|        E     export rendering window to numpy file       |
|        q     return control to python script             |
|        Esc   close the rendering window and continue     |
|        F1    abort execution and exit python kernel      |
| Mouse: Left-click    rotate scene / pick actors          |
|        Middle-click  pan scene                           |
|        Right-click   zoom scene in or out                |
|        Cntrl-click   rotate scene perpendicularly        |
|----------------------------------------------------------|
| Check out documentation at:  https://vtkplotter.embl.es  |
 ==========================================================
    """


    def __init__(self, brain_regions=None, regions_aba_color=False, 
                    neurons=None, tracts=None, add_root=None, verbose=True):
        """[Creates and manages a Plotter instance]
        
        Keyword Arguments:
            brain_regions {[list]} -- [list of brain regions acronyms or ID numebers to be added to the sceme] (default: {None})
            regions_aba_color {[bool]} -- [If true use the Allen Brain Atlas regions coors] (default: {False})
            
            neurons {[list]} -- [list of dictionaries with neurons rendered by mouselight_parser] (default: {None})
            tracts {[list]} -- [list of tractography items, one per experiment] (default: {None})
            add_root {[bool]} -- [if true add semi transparent brain shape to scene. If None the default setting is used] (default: {None})

        """
        BrainRender.__init__(self)
        self.verbose = verbose
        self.regions_aba_color = regions_aba_color

        if add_root is None:
            add_root = DISPLAY_ROOT

        self.plotter = Plotter()

        self.actors = {"regions":{}, "tracts":{}, "neurons":{}, "root":None}

        if brain_regions is not None:
            self.add_brain_regions(brain_regions)

        if neurons is not None:
            self.add_neurons(neurons)

        if tracts is not None:
            self.add_tracts(tracts)

        if add_root:
            self.add_root()
        else:
            self.root = None

        self.rotated = False  # the first time the scene is rendered it must be rotated, the following times it must not be rotated
        self.inset = None  # the first time the scene is rendered create and store the inset here

    def add_actors(self, actors):
        self.plotter.add(actors, render=False)

    def remove_actors(self, actors):
        self.plotter.remove(actors)

    def check_obj_file(self, structure, obj_file):
        # checks if the obj file has been downloaded already, if not it takes care of downloading it
        if not os.path.isfile(obj_file):
                        mesh = self.space.download_structure_mesh(structure_id = structure[0]["id"], 
                                                        ccf_version ="annotation/ccf_2017", 
                                                        file_name=obj_file)

    def add_root(self, render=True):
        structure = self.structure_tree.get_structures_by_acronym(["root"])[0]
        obj_path = os.path.join(models_fld, "root.obj")
        self.check_obj_file(structure, obj_path)
        self.root = self.plotter.load(obj_path, c=ROOT_COLOR, alpha=ROOT_ALPHA) 

        if render:
            self.actors['root'] = self.root

    @staticmethod
    def check_region(region):
        if not isinstance(region, int) and not isinstance(region, str):
            raise ValueError("region must be a list, integer or string")
        else: return True

    def add_brain_regions(self, brain_regions, VIP_regions=None, VIP_color=None): 
        if VIP_regions is None:
            VIP_regions = self.VIP_regions
        if VIP_color is None:
            VIP_color = self.VIP_color

        # check that we have a list
        if not isinstance(brain_regions, list):
            self.check_region(brain_regions)
            brain_regions = [brain_regions]
    
        # loop over all brain regions
        for region in brain_regions:
            self.check_region(region)

            # if it's an ID get the acronym
            if isinstance(region, int):
                region = self.structure_tree.get_region_by_id([region])[0]['acronym']

            if self.verbose: print("Rendering: ({})".format(region))
            
            # get the structure and check if we need to download the object file
            structure = self.structure_tree.get_structures_by_acronym([region])[0]
            obj_file = os.path.join(models_fld, "{}.obj".format(structure["acronym"]))
            self.check_obj_file(structure, obj_file)

            # check which color to assign to the brain region
            if self.regions_aba_color:
                color = [x/255 for x in structure["rgb_triplet"]]
            else:
                if region in VIP_regions:
                    color = VIP_color
                else:
                    color = DEFAULT_STRUCTURE_COLOR


            # Load the object file as a mesh and store the actor
            self.actors["regions"][region] = self.plotter.load(obj_file, c=color, 
                                                                        alpha=DEFAULT_STRUCTURE_ALPHA) 

    def get_actors(self):
        all_actors = []
        for k, actors in self.actors.items():
            if isinstance(actors, dict):
                all_actors.extend(list(actors.values()))
            else:
                all_actors.append(actors)
        return all_actors

    def render(self, interactive=True):
        if not self.rotated:
            roll, azimuth, elevation = 180, -35, -25
            self.rotated = True
        else:
            roll = azimuth = elevation = None

        if DISPLAY_INSET and self.inset is None:
            if self.root is None:
                self.add_root(render=False)

            self.inset = self.root.clone().scale(.5)
            self.inset.alpha(1)
            self.plotter.showInset(self.inset, pos=(0.9,0.2))  

        if VERBOSE:
            print(self.interactive_commands)

        if interactive:
            show(self.get_actors(), interactive=True, roll=roll, azimuth=azimuth, elevation=elevation)  
        else:
            show(*self.get_actors(), interactive=False,  offscreen=True, roll=roll, azimuth=azimuth, elevation=elevation)  


            

# TODO
"""
    Slicing
            if sagittal_slice:
            for a in vp.actors:
                a.cutWithPlane(origin=(0,0,6000), normal=(0,0,-1), showcut=True)

    VideoMaker

"""


if __name__ == "__main__":
    scene = Scene(brain_regions = ["ZI", "PAG", "SCm"])
    scene.render()