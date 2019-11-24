import numpy as np
import os
import random
from vtkplotter import *
import copy
from tqdm import tqdm
import pandas as pd
from vtk import vtkOBJExporter, vtkRenderWindow
from functools import partial
from pathlib import Path
import datetime

from BrainRender.colors import *
from BrainRender.variables import *

from BrainRender.Utils.ABA.connectome import ABA
from BrainRender.Utils.data_io import load_json, load_volume_file
from BrainRender.Utils.data_manipulation import get_coords, flatten_list, get_slice_coord, is_any_item_in_list, mirror_actor_at_point
from BrainRender.Utils import actors_funcs

from BrainRender.Utils.parsers.mouselight import NeuronsParser, edit_neurons
from BrainRender.Utils.parsers.streamlines import parse_streamline
from BrainRender.Utils.parsers.rat import get_rat_mesh_from_region, get_rat_regions_metadata
from BrainRender.Utils.parsers.drosophila import get_drosophila_mesh_from_region, get_drosophila_regions_metadata

from BrainRender.Utils.image import image_to_surface

"""
    The code below aims to create a scene to which actors can be added or removed, changed etc..
    It also facilitates the interaction with the scene (e.g. moving the camera) and the creation of 
    snapshots or animated videos. 
    The class Scene is based on the Plotter class of Vtkplotter: https://github.com/marcomusy/vtkplotter/blob/master/vtkplotter/plotter.py
    and other classes within the same package. 
"""

class Scene(ABA):  # subclass brain render to have acces to structure trees
    VIP_regions = DEFAULT_VIP_REGIONS
    VIP_color = DEFAULT_VIP_COLOR

    ignore_regions = ['retina', 'brain', 'fiber tracts', 'grey']

    camera_params = {"viewup": [0.25, -1, 0]}
    video_camera_params = {"viewup": [0, -1, 0]}

    def __init__(self, brain_regions=None, regions_aba_color=False, 
                    neurons=None, tracts=None, add_root=None, verbose=True, jupyter=False, 
                    display_inset=None, paths_file=None, add_screenshot_button=False, ):
        """[Creates and manages a Plotter instance]
        
        Keyword Arguments:
            brain_regions {[list]} -- [list of brain regions acronyms or ID numebers to be added to the sceme] (default: {None})
            regions_aba_color {[bool]} -- [If true use the Allen Brain Atlas regions coors] (default: {False})
            
            neurons {[str]} -- [path to JSON file for neurons to be rendered by mouselight_parser. Alternatively it can 
                                    be a list of already rendered neurons' actors] (default: {None})
            tracts {[list]} -- [list of tractography items, one per experiment] (default: {None})
            add_root {[bool]} -- [if true add semi transparent brain shape to scene. If None the default setting is used] (default: {None})
            path_file {[str]} -- [Path to a YAML file specifying paths to data folders, to replace default paths] (default: {None})
            add_screenshot_button {[bool]} -- [If true it adds a button that is used to take screenshots] (default: {False})

        """
        ABA.__init__(self, paths_file=paths_file)

        self.verbose = verbose
        self.regions_aba_color = regions_aba_color
        self.jupyter = jupyter 

        if display_inset is None:
            self.display_inset = DISPLAY_INSET
        else:
            self.display_inset = display_inset

        if add_root is None:
            add_root = DISPLAY_ROOT

        # Create camera and plotter
        if WHOLE_SCREEN: 
            sz = "full"
        else: 
            sz = "auto"

        self.plotter = Plotter(axes=4, size=sz, bg=BACKGROUND_COLOR)
        self.actors = {"regions":{}, "tracts":[], "neurons":[], "root":None, "injection_sites":[], "others":[]}
        self._actors = None # store a copy of the actors when manipulations like slicing are done

        if brain_regions is not None:
            self.add_brain_regions(brain_regions)

        if neurons is not None:
            self.add_neurons(neurons)

        if tracts is not None:
            self.add_tractography(tracts)

        if add_root:
            self.add_root(render=True)
        else:
            self.root = None

        self.add_screenshot_button_arg = add_screenshot_button
        self.add_screenshot_button()

        self.rotated = False  # the first time the scene is rendered it must be rotated, the following times it must not be rotated
        self.inset = None  # the first time the scene is rendered create and store the inset here
        self.slider_actors = None # list to hold actors to be affected by opacity slider
        self.is_rendered = False # keep track of if the scene has already been rendered
    
    ####### UTILS
    def check_obj_file(self, structure, obj_file):
        # checks if the obj file has been downloaded already, if not it takes care of downloading it
        if not os.path.isfile(obj_file):
            try:
                mesh = self.space.download_structure_mesh(structure_id = structure["id"], 
                                                ccf_version ="annotation/ccf_2017", 
                                                file_name=obj_file)
                return True
            except:
                print("Could not get mesh for: {}".format(obj_file))
                return False
        else: return True

    @staticmethod
    def check_region(region):
        if not isinstance(region, int) and not isinstance(region, str):
            raise ValueError("region must be a list, integer or string")
        else: return True

    def get_region_color(self, regions):
        if not isinstance(regions, list):
            return self.structure_tree.get_structures_by_acronym([regions])[0]['rgb_triplet']
        else:
            return [self.structure_tree.get_structures_by_acronym([r])[0]['rgb_triplet'] for r in regions]

    def get_structure_parent(self, acronyms):
        if not isinstance(acronyms, list):
            self.check_region(acronyms)
            s = self.structure_tree.get_structures_by_acronym([acronyms])[0]
            if s['id'] in self.structures.id.values:
                return s
            else:
                return self.get_structure_ancestors(s['acronym']).iloc[-1]
        else:
            parents = []
            for region in acronyms:
                self.check_region(region)
                s = self.structure_tree.get_structures_by_acronym(acronyms)[0]

                if s['id'] in self.structures.id.values:
                    parents.append(s)                    
                parents.append(self.get_structure_ancestors(s['acronym']).iloc[-1])
            return parents
    
    def get_structure_childrens(self, acronyms):
        raise NotImplementedError()

    def _get_structure_mesh(self, acronym, plotter=None,  **kwargs):
        if plotter is None: 
            plotter = self.plotter

        structure = self.structure_tree.get_structures_by_acronym([acronym])[0]
        obj_path = os.path.join(self.mouse_meshes, "{}.obj".format(acronym))

        if self.check_obj_file(structure, obj_path):
            mesh = plotter.load(obj_path, **kwargs)
            return mesh
        else:
            return None

    def get_region_from_point(self, p0):
        # given a set of coordinates, get the brain region they are in
        parent = None
        for struct in sorted(list(self.structures.acronym.values)):
            mesh = self._get_structure_mesh(struct).decimate()
            if mesh.isInside(p0):
                parent = struct
                break
        return parent
    
    def get_region_CenterOfMass(self, regions, unilateral=True, hemisphere="right"):
        """[Get the center of mass of the 3d mesh of  (or multiple) brain s. ]
        
        Arguments:
            regions {[str, list]} -- [string or list of string with acronym of brain regions of interest]
            unilateral {[bool]} -- [Get the CoM of the structure in just on hemisphere. Useful for lateralized structures like CA1. ] (default: {True})
            hemisphere {[str]} -- [left or right hemisphere] (default: {"right"})

        Returns:
            coms = {list, dict} -- [if only one regions is passed, then just returns the CoM coordinates for that region. 
                                If a list is passed then a dictionary is returned. ]
        """

        if not isinstance(regions, list): 
            # load mesh corresponding to brain region
            if unilateral:
                mesh = self.get_region_unilateral(regions, hemisphere="left")
            else:
                mesh = self._get_structure_mesh(regions)

            if unilateral and hemisphere.lower() == 'right':
                if self.root is None:
                    self.add_root(render=False)
                return list(np.array(get_coords([np.int(x) for x in mesh.centerOfMass()], mirror=self.root_center[2])).astype(np.int32))
            else:
                return [np.int(x) for x in mesh.centerOfMass()]
        else:
            coms = {}
            for region in regions:
                if unilateral:
                    mesh = self.get_region_unilateral(region, hemisphere="left")
                else:
                    mesh = self._get_structure_mesh(region)
                coms[region] = [np.int(x) for x in mesh.centerOfMass()]
            return coms

    def get_n_rando_points_in_region(self, region, N, max_iters = 1000000):
        if region not in self.actors['regions']:
            raise ValueError("Region {} needs to be rendered first.".format(region))
        
        region_mesh = self.actors['regions'][region]
        region_bounds = region_mesh.bounds()

        points, niters = [], 0
        while len(points) < N and niters < max_iters:
                x = np.random.randint(region_bounds[0], region_bounds[1])
                y = np.random.randint(region_bounds[2], region_bounds[3])
                z = np.random.randint(region_bounds[4], region_bounds[5])
                p = [x, y, z]
                if region_mesh.isInside(p):
                    points.append(p)
                niters += 1
        return points

    def get_region_unilateral(self, region, hemisphere="both", color=None, alpha=None):
        """[Regions meshes are loaded with both hemispheres' meshes. This function splits them in two. ]
        
        Arguments:
            region {[str]} -- [acronym of the brain region]
            hemisphere {[str]} -- [which hemispheres to return, options are "left", "right", and "both"]

        """
        if color is None: color = ROOT_COLOR
        if alpha is None: alpha = ROOT_ALPHA
        bilateralmesh = self._get_structure_mesh(region, c=color, alpha=alpha)

        
        com = bilateralmesh.centerOfMass()   # this will always give a point that is on the midline
        cut = bilateralmesh.cutWithPlane(showcut=True, origin=com, normal=(0, 0, 1))

        right = bilateralmesh.cutWithPlane(showcut=False, origin=com, normal=(0, 0, 1))
        
        # left is the mirror right # WIP
        com = self.get_region_CenterOfMass('root', unilateral=False)[2]
        left = mirror_actor_at_point(right.clone(), com, axis='x')
        
        if hemisphere == "both":
            return left, right
        elif hemisphere == "left":
            return left
        else:
            return right

    def _get_inset(self, **kwargs):
        if "plotter" in list(kwargs.keys()):
            root = self.add_root(render=False, **kwargs)
            inset = root.clone().scale(.5)

        if self.display_inset and self.inset is None:
            if self.root is None:
                self.add_root(render=False, **kwargs)
                self.inset = self.root.clone().scale(.5)
                self.root = None
                self.actors['root'] = None
            else:
                self.inset = self.root.clone().scale(.5)

            self.inset.alpha(1)
            self.plotter.showInset(self.inset, pos=(0.9,0.2))  

    ###### ADD  and EDIT ACTORS TO SCENE
    def add_vtkactor(self, actor):
        self.actors['others'].append(actor)

    def add_from_file(self, filepath, **kwargs):
        actor = load_volume_file(filepath, **kwargs)
        self.actors['others'].append(actor)
        return actor

    def add_root(self, render=True, **kwargs):
        if not render:
            self.root = self._get_structure_mesh('root', c=ROOT_COLOR, alpha=0, **kwargs)
        else:
            self.root = self._get_structure_mesh('root', c=ROOT_COLOR, alpha=ROOT_ALPHA, **kwargs)

        # get the center of the root and the bounding box
        self.root_center = self.root.centerOfMass()
        self.root_bounds = {"x":self.root.xbounds(), "y":self.root.ybounds(), "z":self.root.zbounds()}

        if render:
            self.actors['root'] = self.root

        return self.root

    def add_brain_regions(self, brain_regions, VIP_regions=None, VIP_color=None, 
                        colors=None, use_original_color=False, alpha=None, hemisphere=None): 
        """[Adds rendered brain regions with data from the Allen brain atlas. ]
        
        Arguments:
            brain_regions {[str, list]} -- [List of acronym of brain regions, should include any VIP region. Alternatively numerical IDs can be passed instead of acronym]
        
        Keyword Arguments:
            VIP_regions {list} -- [list of regions acronyms for regions to render differently from other regions] (default: {None})
            VIP_color {[str, color]} -- [Color of VIP regions] (default: {None})
            colors {[str]} -- [Color of other's regions] (default: {None})
            use_original_color {[bool]} -- [if true, color regions by the default allen color] (default: {False})
            alpha {[float]} -- [Transparency of rendered brain regions] (default: {None})
            hemisphere {[str]} -- [If 'left' or 'right' only the mesh in the corresponding hemisphereis rendered ] (default: {False})
        """
        if VIP_regions is None:
            VIP_regions = self.VIP_regions
        if VIP_color is None:
            VIP_color = self.VIP_color
        if alpha is None:
            _alpha = DEFAULT_STRUCTURE_ALPHA
        else: _alpha = alpha

        # check that we have a list
        if not isinstance(brain_regions, list):
            self.check_region(brain_regions)
            brain_regions = [brain_regions]
    
        # check the colors input is correct
        if colors is not None:
            if isinstance(colors[0], list):
                if not len(colors) == len(brain_regions): raise ValueError("when passing colors as a list, the number of colors must match the number of brain regions")
                for col in colors:
                    if not check_colors(col): raise ValueError("Invalide colors in input: {}".format(col))
            else:
                if not check_colors(colors): raise ValueError("Invalide colors in input: {}".format(colors))
                colors = [colors for i in range(len(brain_regions))]

        # loop over all brain regions
        for i, region in enumerate(brain_regions):
            self.check_region(region)

            # if it's an ID get the acronym
            if isinstance(region, int):
                region = self.structure_tree.get_region_by_id([region])[0]['acronym']

            if region in self.ignore_regions or region in list(self.actors['regions'].keys()): continue
            if self.verbose: print("Rendering: ({})".format(region))
            
            # get the structure and check if we need to download the object file
            structure = self.structure_tree.get_structures_by_acronym([region])[0]
            obj_file = os.path.join(self.mouse_meshes, "{}.obj".format(structure["acronym"]))
            
            if not self.check_obj_file(structure, obj_file):
                print("Could not render {}, maybe we couldn't get the mesh?".format(structure["acronym"]))
                continue

            # check which color to assign to the brain region
            if self.regions_aba_color or use_original_color:
                color = [x/255 for x in structure["rgb_triplet"]]
            else:
                if region in VIP_regions:
                    color = VIP_color
                else:
                    if colors is None:
                        color = DEFAULT_STRUCTURE_COLOR
                    elif isinstance(colors, list):
                        color = colors[i]
                    else: color = colors

            if region in VIP_regions:
                alpha = 1
            else:
                alpha = _alpha

            # Load the object file as a mesh and store the actor

            if hemisphere is not None:
                if hemisphere.lower() == "left" or hemisphere.lower() == "right":
                    obj = self.get_region_unilateral(structure["acronym"], hemisphere=hemisphere, color=color, alpha=alpha)
            else:
                obj = self.plotter.load(obj_file, c=color, alpha=alpha) 

            self.actors["regions"][region] =obj

    def add_neurons(self, neurons, display_soma_region=False, soma_regions_kwargs=None, 
                    display_axon_regions=False, 
                    display_dendrites_regions=False, **kwargs):
        """[Adds rendered morphological data of neurons reconstructions downloaded from the Mouse Light project at Janelia. ]
        
        Arguments:
            neurons {[str, list]} -- [Either a string to a JSON file with neurons data, or a list of neurons actors that have already been rendered.]
        
        Keyword Arguments:
            display_soma_region, axon_regions_kwargs, dendrites_regions_kwargs {bool} -- [add the brain region in which the soma is to the scene, or where axons/dendrites go through] (default: {False})
            soma_regions_kwargs {[dict]} -- [dictionary of keywards arguments to pass to self.add_brain_regions] (default: {None})
        
        Raises:
            FileNotFoundError: [description]
            ValueError: [description]
        """
        def runfile(parser, neuron_file, soma_regions_kwargs):
            neurons, regions = parser.render_neurons(neuron_file)
            self.actors["neurons"].extend(neurons)

            # add soma's brain reigons
            if soma_regions_kwargs is None:
                soma_regions_kwargs = {
                    "use_original_color":False, 
                    "alpha":0.5
                }
            if display_soma_region:
                self.add_brain_regions(flatten_list([r['soma'] for r in regions]), **soma_regions_kwargs)
            if display_axon_regions:
                self.add_brain_regions(flatten_list([r['axon'] for r in regions]), **soma_regions_kwargs)
            if display_dendrites_regions:
                self.add_brain_regions(flatten_list([r['dendrites'] for r in regions]), **soma_regions_kwargs)                    
                
        if isinstance(neurons, str):
            if os.path.isfile(neurons):
                parser = NeuronsParser(scene=self, **kwargs)
                runfile(parser, neurons, soma_regions_kwargs)
            else:
                raise FileNotFoundError("The neuron file provided cannot be found: {}".format(neurons))
        elif isinstance(neurons, list):
            if not isinstance(neurons[0], str):
                neurons = edit_neurons(neurons, **kwargs)
                self.actors["neurons"].extend(neurons)
            else:
                # list of file paths
                if not os.path.isfile(neurons[0]): raise ValueError("Expected a list of file paths, got {} instead".format(neurons))
                parser = NeuronsParser(scene=self, **kwargs)
                for nfile in neurons:
                    runfile(parser, nfile, soma_regions_kwargs)
        else:
            if isinstance(neurons, dict):
                neurons = edit_neurons([neurons], **kwargs)
                self.actors["neurons"].extend(neurons)
            else:
                raise ValueError("the 'neurons' variable passed is neither a filepath nor a list of actors: {}".format(neurons))
        return neurons

    def edit_neurons(self, neurons=None, copy=False, **kwargs): 
        """[Edit neurons that have already been rendered. Change color, mirror them etc.]
        
        Keyword Arguments:
            neurons {[list, vtkactor]} -- [lis t of neurons actors to edit, if None all neurons in the scene are edited] (default: {None})
            copy {bool} -- [if true the neurons are copied first and then the copy is edited, otherwise the originals are edited] (default: {False})
        """
        only_soma = False
        if "mirror" in list(kwargs.keys()):
            if kwargs["mirror"] == "soma":
                only_soma = True
            mirror_coord = self.get_region_CenterOfMass('root', unilateral=False)[2]
        else:
            mirror_coord = None

        if neurons is None:
            neurons = self.actors["neurons"]
            if not copy:
                self.actors["neurons"] = []
        elif not isinstance(neurons, list):
            neurons = [neurons]

        if copy:
            copied_neurons = []
            for n in neurons:
                copied = {k:(a.clone() if not isinstance(a, (list, tuple)) and a is not None else []) for k,a in n.items()}
                copied_neurons.append(copied)
            neurons = copied_neurons

        edited_neurons = edit_neurons(neurons, mirror_coord=mirror_coord, only_soma=only_soma, **kwargs)
        self.actors["neurons"].extend(edited_neurons)

    def add_tractography(self, tractography, color=None, display_injection_structure=False, 
                        display_onlyVIP_injection_structure=False, color_by="manual", others_alpha=1, verbose=True,
                        VIP_regions=[], VIP_color="red", others_color="white", include_all_inj_regions=False,
                        extract_region_from_inj_coords=False):
        """[Edit neurons that have already been rendered. Change color, mirror them etc.]
        
        Arguments:
            tractography {[list]} -- [List of dictionaries with tractography data. To get the tractography data use ABA_analyzer.get_traget_projection_tracts_to_target]

        Keyword Arguments:
            display_injection_structure {[Bool]} -- [If true the mesh for the injection structure is rendered] (default: {False})
            colors {color, list} -- [If None default color is used. Alternatively can be either a color or list of colors] (default: {None})
            display_onlyVIP_injection_structure {bool} -- [If true only the injection structures that are in VIP_regions are listed ] (default: {False})
            color_by {str} -- [Specify how the tracts are colored (overrides colors).  options are:
                        - manual: use the value of 'color'
                        - region: color by the ABA RGB color of injection region
                        - target_region: color tracts and regions in VIP_regions with VIP_coor and others with others_color] (default: {False})
            include_all_inj_regions {bool} -- [If true use all regions marked as injection region, otherwise only the primary one] (default: {False})
            extract_region_from_inj_coords {bool} -- [f True instead of using the allen provided injection region metadata extracts the injection structure from the coordinates.] (default: {False})            

            VIP_regions {list} -- [Optional. List of brain regions that can be rendered differently from 'others'] (default: {False})
            VIP_color {str} -- [Color for VIP regions] 
            others_color {str} -- [Color for 'others' regions] 
            verbose {bool} -- [If true print useful info during rendering] (default: {True})
            others_alpha {float} -- [Transparency of 'others' structures] (default: {False})
        """

        # check argument
        if not isinstance(tractography, list):
            if isinstance(tractography, dict):
                tractography = [tractography]
            else:
                raise ValueError("the 'tractography' variable passed must be a list of dictionaries")
        else:
            if not isinstance(tractography[0], dict):
                raise ValueError("the 'tractography' variable passed must be a list of dictionaries")

        if not isinstance(VIP_regions, list): raise ValueError("VIP_regions should be a list of acronyms")

        # check coloring mode used and prepare a list COLORS to use for coloring stuff
        if color_by == "manual":
            # check color argument
            if color is None:
                color = TRACT_DEFAULT_COLOR
                COLORS = [color for i in range(len(tractography))]
            elif isinstance(color, list):
                if not len(color) == len(tractography):
                    raise ValueError("If a list of colors is passed, it must have the same number of items as the number of tractography traces")
                else:
                    for col in color:
                        if not check_colors(col): raise ValueError("Color variable passed to tractography is invalid: {}".format(col))

                    COLORS = color                
            else:
                if not check_colors(color):
                    raise ValueError("Color variable passed to tractography is invalid: {}".format(color))
                else:
                    COLORS = [color for i in range(len(tractography))]

        elif color_by == "region":
            COLORS = [self.get_region_color(t['structure-abbrev']) for t in tractography]

        elif color_by == "target_region":
            if not check_colors(VIP_color) or not check_colors(others_color): raise ValueError("Invalid VIP or other color passed")
            try:
                if include_all_inj_regions:
                    COLORS = [VIP_color if is_any_item_in_list( [x['abbreviation'] for x in t['injection-structures']], VIP_regions) else others_color for t in tractography]
                else:
                    COLORS = [VIP_color if t['structure-abbrev'] in VIP_regions else others_color for t in tractography]
            except:
                raise ValueError("Something went wrong while getting colors for tractography")
        else:
            raise ValueError("Unrecognised 'color_by' argument {}".format(color_by))
        
        # add actors to represent tractography data
        actors, structures_acronyms = [], []
        if VERBOSE and verbose:
            print("Structures found to be projecting to target: ")

        # Loop over injection experiments
        for i, (t, color) in enumerate(zip(tractography, COLORS)):
            # Use allen metadata 
            if include_all_inj_regions:
                inj_structures = [x['abbreviation'] for x in t['injection-structures']]
            else:
                inj_structures = [self.get_structure_parent(t['structure-abbrev'])['acronym']]

            # show brain structures in which injections happened
            if display_injection_structure:
                if not is_any_item_in_list(inj_structures, list(self.actors['regions'].keys())):
                    if display_onlyVIP_injection_structure and is_any_item_in_list(inj_structures, VIP_regions):
                        self.add_brain_regions([t['structure-abbrev']], colors=color)
                    elif not display_onlyVIP_injection_structure:
                        self.add_brain_regions([t['structure-abbrev']], colors=color)
                    
            if VERBOSE and verbose and not is_any_item_in_list(inj_structures, structures_acronyms):
                print("     -- ({})".format(t['structure-abbrev']))
                structures_acronyms.append(t['structure-abbrev'])

            # get tractography points and represent as list
            if color_by == "target_region" and not is_any_item_in_list(inj_structures, VIP_regions):
                alpha = others_alpha
            else:
                alpha = TRACTO_ALPHA

            if alpha == 0: continue # skip transparent ones

            # check if we need to manually check injection coords
            if extract_region_from_inj_coords:
                try:
                    region = self.get_region_from_point(t['injection-coordinates'])
                    if region is None: continue
                    inj_structures = [self.get_structure_parent(region)['acronym']]
                except:
                    raise ValueError(self.get_region_from_point(t['injection-coordinates']))
                if inj_structures is None: continue
                elif isinstance(extract_region_from_inj_coords, list):
                    # check if injection coord are in one of the brain regions in list, otherwise skip
                    if not is_any_item_in_list(inj_structures, extract_region_from_inj_coords):
                        continue

            # represent injection site as sphere
            actors.append(Sphere(pos=t['injection-coordinates'],
                             c=color, r=INJECTION_VOLUME_SIZE*t['injection-volume'], alpha=TRACTO_ALPHA))

            points = [p['coord'] for p in t['path']]
            actors.append(shapes.Tube(points, r=TRACTO_RADIUS, c=color, alpha=alpha, res=TRACTO_RES))

        self.actors['tracts'].extend(actors)

    def add_streamlines(self, sl_file,  colorby=None, color_each=False, *args, **kwargs):
        """
        [Render streamline data downloaded from https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html]
        Arguments:
            sl_file {[str, list]} -- [Either a string to a JSON file with streamline data, or a list of json files.]
        
        Keyword Arguments:
            colorby {[str]} -- [Acronym of brain region to use to color the streamline data] (default: {None})
            color_each {[bool]} -- [If true streamlines for each experiment are shown in a different color. 
                                    If a color is passed as color="colorname", shades of that color are used] (default: {False})

        """
        color = None
        if not color_each:
            if colorby is not None:
                try:
                    color = self.structure_tree.get_structures_by_acronym([colorby])[0]['rgb_triplet']
                    if "color" in kwargs.keys():
                        del kwargs["color"]
                except:
                    raise ValueError("Could not extract color for region: {}".format(colorby))
        else:
            if colorby is not None:
                color = kwargs.pop("color", None)
                try:
                    get_n_shades_of(color, 1)
                except:
                    raise ValueError("Invalide color argument: {}".format(color))

        if isinstance(sl_file, list):
            if isinstance(sl_file[0], (str, pd.DataFrame)): # we have a list of files to add
                for slf in tqdm(sl_file):
                    if not color_each:
                        if color is not None:
                            if isinstance(slf, str):
                                streamlines = parse_streamline(filepath=slf, *args, color=color, **kwargs)
                            else:
                                streamlines = parse_streamline(data=slf, *args, color=color, **kwargs)
                        else:
                            if isinstance(slf, str):
                                streamlines = parse_streamline(filepath=slf, *args, **kwargs)
                            else:
                                streamlines = parse_streamline(data=slf,  *args, **kwargs)
                    else:
                        if color is not None:
                            col = get_n_shades_of(color, 1)[0]
                        else:
                            col = get_random_colors(n_colors=1)
                        if isinstance(slf, str):
                            streamlines = parse_streamline(filepath=slf, color=col, *args, **kwargs)
                        else:
                            streamlines = parse_streamline(data= slf, color=col, *args, **kwargs)
                    self.actors['tracts'].extend(streamlines)
            else:
                raise ValueError("unrecognized argument sl_file: {}".format(sl_file))
        else:
            if not isinstance(sl_file, (str, pd.DataFrame)): raise ValueError("unrecognized argument sl_file: {}".format(sl_file))
            if not color_each:
                if isinstance(sl_file, str):
                    streamlines = parse_streamline(filepath=sl_file, *args,  **kwargs)
                else:
                    streamlines = parse_streamline(data=sl_file, *args,  **kwargs)
            else:
                if color is not None:
                    col = get_n_shades_of(color, 1)[0]
                else:
                    col = get_random_colors(n_colors=1)
                if isinstance(sl_file, str):
                    streamlines = parse_streamline(filepath=sl_file, color=col, *args, **kwargs)
                else:
                    streamlines = parse_streamline(data=sl_file, color=col, *args, **kwargs)
            self.actors['tracts'].extend(streamlines)

    def add_injection_sites(self, experiments, color=None):
        """[Creates Spherse at the location of injections with a volume proportional to the injected volume]
        
        Arguments:
            experiments {[list]} -- [list of dictionaries with experiments metadata]
        """
        # check arguments
        if not isinstance(experiments, list):
            raise ValueError("experiments must be a list")
        if not isinstance(experiments[0], dict):
            raise ValueError("experiments should be a list of dictionaries")

        #c= cgeck color
        if color is None:
            color = INJECTION_DEFAULT_COLOR

        injection_sites = []
        for exp in experiments:
            injection_sites.append(Sphere(pos=(exp["injection_x"], exp["injection_y"], exp["injection_z"]),
                    r = INJECTION_VOLUME_SIZE*exp["injection_volume"]*3, 
                    c=color
                    ))

        self.actors['injection_sites'].extend(injection_sites)

    def add_sphere_at_point(self, pos=[0, 0, 0], radius=100, color="black", alpha=1):
        self.actors['others'].append(Sphere(pos=pos, r=radius, c=color, alpha=alpha))

    def add_cells_from_file(self, filepath, hdf_key=None, color="red",
                            radius=25, res=3):
        """
            [Load location of cells from a file (csv and HDF) and render as spheres aligned to the root mesh. ]
            Arguments:
                filepath {str} -- [Path to the .csv or .h5 file with cell locations]
            
            Keyword Arguments:
                hdf_key {[str]} -- [key used for parsing HDF file] (default: {None})
                color {[str, color]} -- [color of the spheres used to render the cells.] (default: {red})
                radius {[int]} -- [radius of the sphere used to render cells] (default: {25})
                res {[int]} -- [resolution of the spheres. The lower the faster the rendering] (default: {3})
        """
        csv_suffix = ".csv"
        supported_formats = HDF_SUFFIXES + [csv_suffix]

        #  check that the filepath makes sense
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(filepath)

        # check that the file is of the supported types
        if filepath.suffix in supported_formats:
            # parse file and load cell locations
            if filepath.suffix in HDF_SUFFIXES:
                if hdf_key is None:
                    hdf_key = DEFAULT_HDF_KEY
                try:
                    cells = pd.read_hdf(filepath, key=hdf_key)
                except TypeError:
                    if hdf_key == DEFAULT_HDF_KEY:
                        raise ValueError(
                            f"The default identifier: {DEFAULT_HDF_KEY} "
                            f"cannot be found in the hdf file. Please supply "
                            f"a key using 'scene.add_cells_from_file(filepath, "
                            f"hdf_key='key'")
                    else:
                        raise ValueError(
                            f"The key: {hdf_key} cannot be found in the hdf "
                            f"file. Please check the correct identifer.")
            elif filepath.suffix == csv_suffix:
                cells = pd.read_csv(filepath)
            self.add_cells(cells, color=color, radius=radius, res=res)

        elif filepath.suffix == ".pkl":
            cells = pd.read_picle(filepath)
            self.add_cells(cells, color=color, radius=radius, res=res)
        else:
            raise NotImplementedError(
                f"File format: {filepath.suffix} is not currently supported. "
                f"Please use one of: {supported_formats}")

    def add_cells(self, coords, color="red", radius=25, res=3): 
        """
            [Load location of cells from a file (csv and HDF) and render as spheres aligned to the root mesh. ]
            Arguments:
                coords {pd.DataFrame, list} -- [Either a dataframe of cell locations with columns 'x', 'y' and 'z' or a list of lists, 
                                                each with the x,y,z coordinates of a cell]
            
            Keyword Arguments:
                color {[str, color]} -- [color of the spheres used to render the cells.] (default: {red})
                radius {[int]} -- [radius of the sphere used to render cells] (default: {25})
                res {[int]} -- [resolution of the spheres. The lower the faster the rendering] (default: {3})
        """
        if isinstance(coords, pd.DataFrame):
            coords = [[x, y, z] for x,y,z in zip(coords['x'].values, coords['y'].values, coords['z'].values)]
        spheres = Spheres(coords, c=color, r=radius, res=res)
        self.actors['others'].append(spheres)

    def add_image(self, image_file_path, color=None, alpha=None,
                  obj_file_path=None, voxel_size=1, orientation="saggital",
                  invert_axes=None, extension=".obj", step_size=2,
                  keep_obj_file=True, override='use', smooth=True):

        """
            [Loads a 3d image and processes it to extract mesh coordinates. Mesh coordinates are extracted with
            a fast marching algorithm and saved to a .obj file. This file is then used to render the mesh.]

            Arguments:
                image_file_path {str} -- [Path to 3d image data]
            
            Keyword Arguments:
                hdf_key {[str]} -- [key used for parsing HDF file] (default: {None})
                color {[str, color]} -- [color of rendered mesh. If None, random is used.] (default: {None})
                alpha {[int]} -- [transparency of rendered mesh. If None, default is used.] (default: {None})
                obj_file_path {[str]} -- [path in which to save .obj file. If None path is based on image_file_path] (default: {None})

                voxel_size {[float]} -- [Voxel size of the image (in um). Only isotropic voxels supported currently] (default: {1})
                orientation {[str]} -- [Used to orient 3d image.] (default: {saggital})
                invert_axes {[tuple]} -- [Tuple of axes to invert (if not in the same orientation as the atlas] (default: {None})
                extension {[str]} -- [Extension of the .obj file, others can be used.] (default: {.obj})
                step_size {[int]} -- [Used in marching algorithm to process image data.] (default: {2})
                keep_obj_file {[bool]} -- [if false, the .obj file is deleted after having used it.] (default: {True})
                overwrite {[str]} -- [Allowed values:
                                        'use': if a .obj found matching the image_file_path, use that and skip processing the image, 
                                        'overwrite': if a .obj found matching the image_file_path, process image and overwrite it,
                                        'catch': if a .obj found matching the image_file_path, throw error.] (default: {None})
                smooth {[bool]} -- [If true the rendered mesh is smoothed.] (default: {True})

        """

        # Check args
        if color is None: color = get_random_colors() # get a random color
        
        if alpha is None:
            alpha = DEFAULT_STRUCTURE_ALPHA

        if obj_file_path is None:
            obj_file_path = os.path.splitext(image_file_path)[0] + extension

        if os.path.isinstance(obj_file_path):
            if overwrite == "use":
                print("Found a .obj file that matches your input data. Rendering that instead.")
                print("If you would like to change this behaviour, change the 'overwrite' argument.")
            elif overwrite == "overwrite":
                print("Found a .obj file that matches your input data. Overriding it.")
                print("If you would like to change this behaviour, change the 'overwrite' argument.")
                # Process the image and save as .obj file
                image_to_surface(image_file_path, obj_file_path, voxel_size=voxel_size,
                                orientation=orientation, invert_axes=invert_axes,
                                step_size=step_size)
            elif overwrite == "catch":
                raise FileExistsError("The .obj file exists alread, to overwrite change the 'overwrite' argument.")
            else:
                raise ValueError("Unrecognized value for argument overwrite: {}".format(overwrite))

        # render obj file, smooth and clean up.
        actor = self.add_from_file(obj_file_path, c=color, alpha=alpha)

        if smooth:
            actors_funcs.smooth(actor)

        if not keep_obj_file:
            os.remove(obj_file_path)

    def edit_actors(self, actors, **kwargs):
        if not isinstance(actors, list):
            actors = list(actors)
        
        for actor in actors:
            actors_funcs.edit_actor(actor, **kwargs)

    ####### MANIPULATE SCENE
    def add_screenshot_button(self):
        button_func = partial(self._take_screenshot, self.output_screenshots)

        bu = self.plotter.addButton(
            button_func,
            pos=(0.125, 0.95),  # x,y fraction from bottom left corner
            states=["Screenshot"],
            c=["white"],
            bc=["darkgray"], 
            font="courier",
            size=18,
            bold=True,
            italic=False,
        )

    @staticmethod
    def slider_func(scene, widget, event):
        # function used to change the transparency of meshes according to slider value (see self.add_slider())
        value = widget.GetRepresentation().GetValue()
        for actor in scene.slider_actors:
            actor.alpha(value)

    def add_slider(self, brain_regions=None, actors=None):
        """[Creates a slider in the scene that can be used to adjust the transparency of select actors. 
        Actors can be passed directly to add_slider or added in a second moment using add?actors_to_slider]
        
        Keyword Arguments:
            brain_regions {[list]} -- [List of strings with acronyms of brain regions to be added to the slider] (default: {None})
            actors {[type]} -- [list of vtk plotter actors to be added to the slider] (default: {None})
        """
        # Add actors to slider function
        self.add_actors_to_slider(brain_regions=brain_regions, actors=actors)

        # create slider function
        sfunc = partial(self.slider_func, self)

        # Create slider
        self.plotter.addSlider2D(
            sfunc, 
            xmin=0.01, 
            xmax=0.99, 
            value=0.5,
            pos=4, 
            c="white", 
            title="opacity")

    def add_actors_to_slider(self,  brain_regions=None, actors=None):
        """[Adds actors to the list of actors whose transparency is affected by the slider]
        
        Keyword Arguments:
            brain_regions {[list]} -- [List of strings with acronyms of brain regions to be added to the slider] (default: {None})
            actors {[type]} -- [list of vtk plotter actors to be added to the slider] (default: {None})
        """
        if self.slider_actors is None:
            # parse arguments
            if actors is None:
                self.slider_actors = [] # this list will store all actors that will be affected by the slider value
            else:
                self.slider_actors = list(actors)
        else:
            if actors is not None:
                self.slider_actors.extend(list(actors))
        
        # Get actors that will have to be changed by the slider
        if brain_regions is not None:
            if not isinstance(brain_regions,list): brain_regions = list(brain_regions)
            if 'root' in brain_regions:
                self.slider_actors.append(self.actors['root'])
                brain_regions.pop(brain_regions.index('root'))
            
            # Get other brain regions
            regions_actors = [act for r,act in self.actors['regions'].items() if r in brain_regions]
        self.slider_actors.extend(regions_actors)

    def Slice(self, axis="x", j=0, onlyroot=False): 
        """
            [Slice all actors in scene at one coordinate along a defined axis]

            Keyword Arguments:
                axis {[str]} -- [Possible values:       x -> coronal
                                                        y -> horizontal
                                                        z -> sagittal] (default: {None})
                k {[float]} -- [Number between 0 and 1 to indicate position along the selected axis]
                onlyroot {[bool]} -- [If True only the root actor is sliced] {default: False}
        """
        # check arguments
        if not isinstance(axis, str):
            if not isinstance(axis, list):
                raise ValueError("Unrecognised axis for slicing actors: {}".format(axis))
        else:
            axis = [axis]

        if not isinstance(j, (list, tuple)):
            j = [j for _ in range(len(axis))]
        elif isinstance(j, (list, tuple)) and len(j)!= len(axis) :
            raise ValueError("When slicing over multiple axes, pass a list of values for the slice number j (or a single value). The list must have the same length as the axes list")

        # store a copy of original actors
        self._actors = self.actors.copy()

        # Check if root is in scene to get the center of the root
        if self.root is None:
            self.add_root(render=False)

        # slice actors
        if not onlyroot:
            all_actors = self.get_actors()
        else:
            all_actors = [self.root]

        for actor in all_actors:
            for ax, i in zip(axis, j):
                if ax.lower() == "x":
                    normal = [1, 0, 0]
                    pos = [get_slice_coord(self.root_bounds['x'], i), 0, 0]
                elif ax.lower() == "y":
                    normal = [0, 1, 0]
                    pos = [0, get_slice_coord(self.root_bounds['y'], i), 0]
                elif ax.lower() == "z":
                    normal = [0, 0, 1]
                    pos = [0, 0, get_slice_coord(self.root_bounds['z'], i)]
                else:
                    raise ValueError("Unrecognised ax for slicing actors: {}".format(ax))
                actor = actor.cutWithPlane(origin=pos, normal=normal)

    def ortho_views(self):
        self.render(interactive=False)
        closeWindow()

        # create a new scene with top and side views of the scene
        if self.plotter is None:
            print("nothing to render, populate scene first")
            return

        mv = Plotter(N=2, axes=4, size="auto", sharecam=False)

        # # TODO make root inset appear
        # self._get_inset(plotter=top)
        # self._get_inset(plotter=side)

        # mv.add(self.get_actors())
        mv.add(self.get_actors())

        mv.show(mv.actors, at=0, zoom=1.15, axes=4, roll=180,  interactive=False, camera=dict(viewup=[0, -1, 0]))    
        mv.show(mv.actors, at=1, zoom=10, axes=4, roll=180, interactive=False, camera=dict(viewup=[0, 0, 0]))

        interactive()

    def _rotate_actors(self):
        # Allen meshes are loaded upside down so we need to rotate actors by 180 degrees
        for actor in self.get_actors():
            if actor is None: continue
            actor.rotateZ(180)

    ####### RENDER SCENE
    def apply_render_style(self):
        actors = self.get_actors()

        for actor in actors:
            if actor is not None:
                actor.lighting(style=SHADER_STYLE)

    def get_actors(self):
        all_actors = []
        for k, actors in self.actors.items():
            if isinstance(actors, dict):
                if len(actors) == 0: continue
                all_actors.extend(list(actors.values()))
            elif isinstance(actors, list):
                if len(actors) == 0: continue
                for act in actors:
                    if isinstance(act, dict):
                        all_actors.extend(flatten_list(list(act.values())))
                    elif isinstance(act, list):
                        all_actors.extend(act)
                    else: 
                        all_actors.append(act)
            else:
                all_actors.append(actors)
        return all_actors

    def render(self, interactive=True, video=False):
        self.apply_render_style()

        if not self.rotated:
            roll, azimuth, elevation = 0, -35, 0
            self.rotated = True
        else:
            roll = azimuth = elevation = None

        if VERBOSE and not self.jupyter:
            print(INTERACTIVE_MSG)
        elif self.jupyter:
            print("\n\npress 'Esc' to Quit")
        else:
            print("\n\npress 'q' to Quit")

        if WHOLE_SCREEN:
            zoom = 1.85
        else:
            zoom = 1.5

        self._get_inset()

        self.is_rendered = True

        if interactive and not video:
            show(*self.get_actors(), interactive=False, camera=self.camera_params, azimuth=azimuth, zoom=zoom)  
        elif video:
            show(*self.get_actors(), interactive=False, offscreen=True, camera=self.video_camera_params, zoom=2.5)  
        else:
            show(*self.get_actors(), interactive=False,  offscreen=True, camera=self.camera_params, azimuth=azimuth, zoom=zoom)  

        if self.add_screenshot_button_arg:
            self.add_screenshot_button()
        
        if interactive and not video:
            show(*self.get_actors(), interactive=True, camera=self.camera_params)

    def _add_actors(self): # TODO fix this
        if self.plotter.renderer is None:
            return
        for actor in self.get_actors():
            self.plotter.renderer.AddActor(actor)

    ####### EXPORT SCENE + screenshot
    def export(self, save_dir=None, savename="exported_scene", exportas="obj"):
        """[Exports the scene as a numpy file]
        
        Keyword Arguments:
            save_dir {[str]} -- [path to folder, if none default output folder is used] (default: {None})
            savename {str} -- [filename, can not include ".npy"] (default: {"exported_scene"})
        
        Raises:
            ValueError: [description]
        """
        if save_dir is None:
            save_dir = self.output_scenes
        
        if not os.path.isdir(save_dir):
            raise ValueError("Save folder not valid: {}".format(save_dir))

        if not isinstance(exportas, str): raise ValueError("Unrecognised argument exportas {}".format(exportas))
        exportas = exportas.lower()

        if exportas == 'obj':
            savename = savename.split(".")[0]
        elif exportas == 'npy':
            if "." in savename and not "npy" in savename:
                raise ValueError("Savename should have format: .npy when exporting as numpy")
            elif not "." in savename:
                savename = "{}.npy".format(savename)
        else:
            raise ValueError("can only export as OBJ and NPY for now, not: {}".format(exportas))
        
        curdir = os.getcwd()
        os.chdir(save_dir)

        if exportas == 'npy':
            exportWindow(savename)
        else:
            # Create a new vtkplotter window and add scene's renderer to it 
            rw = vtkRenderWindow()

            if self.plotter.renderer is None: # need to render the scene first
                self.render(interactive=False)
                self._rotate_actors()

                closeWindow()

            rw.AddRenderer(self.plotter.renderer)

            w = vtkOBJExporter()
            w.SetFilePrefix(savename)
            w.SetRenderWindow(rw)
            w.Write()

        # Change back to original dir
        os.chdir(curdir)

        if VERBOSE:
            print("Save scene in {} with filename {}".format(save_dir, savename))

    def export_for_web(self, save_dir=None, filename='scene'):
        # This exports the scene and generates 2 files:
        # embryo.x3d and an example embryo.html to inspect in the browser
        if save_dir is None:
            save_dir = self.output_scenes
        
        if not os.path.isdir(save_dir):
            raise ValueError("Save folder not valid: {}".format(save_dir))

        curdir = os.getcwd()
        os.chdir(save_dir)
        exportWindow('{}.x3d'.format(filename))
        os.chdir(curdir)

    @staticmethod
    def _take_screenshot(default_fld, filename="screenshot.png", scale=1, large=True, savefld=None):
        """[Takes a screenshot of the current scene's view]
        
        Keyword Arguments:
            default_fld {[str]} -- [default path to directory in which to save screenshot if savefld is None]
            filename {str} -- [filename, supported formats: png, jpg, svg] (default: {"screenshot.png"})
            scale {int} -- [In theory values >1 should increase resolution, but it seems to be buggy] (default: {"1"})
            large {bool} -- [Should increase resolution] (default: {"True"})
            savefld {str} -- [alternative folder in which to save the screenshot.] (default: {"None"})
        
        Raises:
            ValueError: [description]
        """
        # Get file name
        if ".png" not in filename and ".svg" not in filename and ".jpg" not in filename:
            raise ValueError("Unrecognized image format. Should be either .png, .svg or .jpg.")
        if savefld is None:
            savefld = default_fld
        filename = os.path.join(savefld, filename)

        # Check if a file with this name exists, change name if it does
        if os.path.isfile(filename):
            f, ext = os.path.splitext(filename)
            now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f + now + ext

        # Get resolution settings
        settings.screeshotLargeImage = large
        settings.screeshotScale = scale

        # take screenshot
        screenshot(filename)
        print("Saved screenshot at: {}".format(filename))

    def take_screenshot(self, **kwargs):
        # for args definition check: self._take_screenshot
        self._take_screenshot(self.output_screenshots, **kwargs)

class RatScene(Scene): # Subclass of Scene to override some methods for Rat data
    def __init__(self, *args, **kwargs):
        Scene.__init__(self,*args, add_root=False, display_inset=False, **kwargs)

        self.structures = get_rat_regions_metadata(self.metadata)
        self.structures_names = list(self.structures['Name'].values)

    def print_structures(self):
        ids, names = self.structures.Id.values, self.structures['Name'].values
        sort_idx = np.argsort(names)
        ids, names = ids[sort_idx], names[sort_idx]
        [print("(id: {}) - {}".format(a, n)) for a,n in zip(ids, names)]

    def add_brain_regions(self, brain_regions, use_original_color=False,
                            color=None, alpha=1, hemisphere=None): 
            """[Override Scnee.add_brain_reigions to get rat data. Adds rendered brain regions with data from the Allen brain atlas. ]
            
            Arguments:
                brain_regions {[str, list]} -- [List of acronym of brain regions, should include any VIP region. Alternatively numerical IDs can be passed instead of acronym]
            
            Keyword Arguments:
                color {[str, list]} -- [Color of other's regions] (default: {None})
                alpha {[float]} -- [Transparency of rendered brain regions] (default: {None})
                hemisphere {[str]} -- [If 'left' or 'right' only the mesh in the corresponding hemisphereis rendered ] (default: {False})
            """

            if alpha is None:
                alpha = DEFAULT_STRUCTURE_ALPHA

            if not isinstance(brain_regions, list):
                brain_regions = [brain_regions]

            if color is None:
                color = [DEFAULT_STRUCTURE_COLOR for region in brain_regions]
            elif isinstance(color[0], (list, tuple)):
                if not len(color) == len(brain_regions): 
                    raise ValueError("When passing a list of colors, the number of colors should be the same as the number of regions")
            else:
                color = [color for region in brain_regions]

            # loop over all brain regions
            for i, (col, region) in enumerate(zip(color, brain_regions)):
                # Load the object file as a mesh and store the actor
                obj = get_rat_mesh_from_region(region, self.folders,  c=col, alpha=alpha, use_original_color=use_original_color)
                if obj is not None:
                    self.actors["regions"][region] = obj

                if VERBOSE:
                    print("rendered {}".format(region))

class DrosophilaScene(Scene): # Subclass of Scene to override some methods for Drosophila data
    def __init__(self, *args, add_root=True, **kwargs):
        Scene.__init__(self,*args, add_root=False, display_inset=False, **kwargs)

        if add_root:
            self.add_brain_regions("root", color=ROOT_COLOR, alpha=ROOT_ALPHA)

        self.structures = get_drosophila_regions_metadata(self.metadata)
        self.structures_acronyms = sorted(list(self.structures['acronym'].values))

    def print_structures(self):
        ids, names, acros = self.structures.Id.values, self.structures['name'].values, self.structures['acronym'].values
        sort_idx = np.argsort(ids)
        ids, names, acros = ids[sort_idx], names[sort_idx], acros[sort_idx]
        [print("(id: {}) - {} - {}".format(a, acr, n)) for a, acr, n in zip(ids, acros, names)]

    def add_brain_regions(self, brain_regions, use_random_color=False,
                            color=None, alpha=1, hemisphere=None): 
            """[Override Scnee.add_brain_reigions to get rat data. Adds rendered brain regions with data from the Allen brain atlas. ]
            
            Arguments:
                brain_regions {[str, list]} -- [List of acronym of brain regions, should include any VIP region. Alternatively numerical IDs can be passed instead of acronym]
            
            Keyword Arguments:
                color {[str, list]} -- [Color of other's regions] (default: {None})
                alpha {[float]} -- [Transparency of rendered brain regions] (default: {None})
                hemisphere {[str]} -- [If 'left' or 'right' only the mesh in the corresponding hemisphereis rendered ] (default: {False})
            """

            if alpha is None:
                alpha = DEFAULT_STRUCTURE_ALPHA

            if not isinstance(brain_regions, list):
                brain_regions = [brain_regions]

            if not use_random_color:
                if color is None:
                    color = [DEFAULT_STRUCTURE_COLOR for region in brain_regions]
                elif isinstance(color[0], (list, tuple)):
                    if not len(color) == len(brain_regions): 
                        raise ValueError("When passing a list of colors, the number of colors should be the same as the number of regions")
                else:
                    color = [color for region in brain_regions]
            else:
                color = get_random_colors(n_colors=len(brain_regions))

            # loop over all brain regions
            for i, (col, region) in enumerate(zip(color, brain_regions)):
                # Load the object file as a mesh and store the actor
                obj = get_drosophila_mesh_from_region(region, self.folders, c=col, alpha=alpha)
                if obj is not None:
                    self.actors["regions"][region] = obj

                if VERBOSE:
                    print("rendered {}".format(region))



class LoadedScene:
    def __init__(self, filepath=None):
        if filepath is not None:
            self.load_scene(filepath)
        else:
            self.plotter = None

    def load_scene(self, filepath):
        if not os.path.isfile(filepath) or not ".npy" in filepath:
            raise ValueError("Invalid file path: {}".format(filepath))

        self.plotter = importWindow(filepath)

    def render(self):
        if self.plotter is None:
            print("Nothing to render, need to load a scene first")
        else:
            self.plotter.show()


class DualScene:
    # A class that manages two scenes to display side by side
    def __init__(self, *args, **kwargs):
        self.scenes = [Scene( *args, **kwargs), Scene( *args, **kwargs)]

    def render(self):
        mv = Plotter(N=2, axes=4, size="auto", sharecam=True)

        actors = []
        for scene in self.scenes:
            scene_actors = scene.get_actors() 
            actors.append(scene_actors)
            mv.add(scene_actors)

        mv.show(actors[0], at=0, zoom=1.15, axes=4, roll=180,  interactive=False)    
        mv.show(actors[1], at=1,  interactive=False)
        interactive()


class MultiScene:
    def __init__(self, N,  *args, **kwargs):
        self.scenes = [Scene( *args, **kwargs) for i in range(N)]
        self.N = N

    def render(self, _interactive=True,  **kwargs):
        if self.N > 4:
            print("Rendering {} scenes. Might take a few minutes.".format(self.N))
        mv = Plotter(N=self.N, axes=4, size="auto", sharecam=True)

        actors = []
        for i, scene in enumerate(self.scenes):
            scene_actors = scene.get_actors() 
            actors.append(scene_actors)
            mv.add(scene_actors)

        for i, scene_actors in enumerate(actors):
            mv.show(scene_actors, at=i,  interactive=False)
        
        print("Rendering complete")
        if _interactive:
            interactive()


