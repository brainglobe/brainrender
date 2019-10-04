import numpy as np
import os
from vtkplotter import *
import copy
from tqdm import tqdm
import pandas as pd
from vtk import vtkOBJExporter, vtkRenderWindow

from BrainRender.Utils.data_io import load_json, load_volume_file
from BrainRender.Utils.data_manipulation import get_coords, flatten_list, get_slice_coord, is_any_item_in_list, mirror_actor_at_point
from BrainRender.colors import *
from BrainRender.variables import *
from BrainRender.ABA_analyzer import ABA
from BrainRender.Utils.mouselight_parser import NeuronsParser, edit_neurons
from BrainRender.settings import *
from BrainRender.Utils.streamlines_parser import parse_streamline, extract_ids_from_csv
from BrainRender.Utils.rat_brain_parser import get_rat_mesh_from_region, get_rat_regions_metadata

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

    """
            - pos, `(list)`,  the position of the camera in world coordinates
            - focalPoint `(list)`, the focal point of the camera in world coordinates
            - viewup `(list)`, the view up direction for the camera
            - distance `(float)`, set the focal point to the specified distance from the camera position.
            - clippingRange `(float)`, distance of the near and far clipping planes along the direction
                of projection.
            - parallelScale `(float)`,
                scaling used for a parallel projection, i.e. the height of the viewport
                in world-coordinate distances. The default is 1. Note that the "scale" parameter works as
                an "inverse scale", larger numbers produce smaller images.
                This method has no effect in perspective projection mode.
            - thickness `(float)`,
                set the distance between clipping planes. This method adjusts the far clipping
                plane to be set a distance 'thickness' beyond the near clipping plane.
            - viewAngle `(float)`,
                the camera view angle, which is the angular height of the camera view
                measured in degrees. The default angle is 30 degrees.
                This method has no effect in parallel projection mode.
                The formula for setting the angle up for perfect perspective viewing is:
                angle = 2*atan((h/2)/d) where h is the height of the RenderWindow
                (measured by holding a ruler up to your screen) and d is the distance
                from your eyes to the screen.
    """
    camera_params = {"viewup": [0.25, -1, 0]}
    video_camera_params = {"viewup": [0, -1, 0]}

    def __init__(self, brain_regions=None, regions_aba_color=False, 
                    neurons=None, tracts=None, add_root=None, verbose=True, jupyter=False, display_inset=None):
        """[Creates and manages a Plotter instance]
        
        Keyword Arguments:
            brain_regions {[list]} -- [list of brain regions acronyms or ID numebers to be added to the sceme] (default: {None})
            regions_aba_color {[bool]} -- [If true use the Allen Brain Atlas regions coors] (default: {False})
            
            neurons {[str]} -- [path to JSON file for neurons to be rendered by mouselight_parser. Alternatively it can 
                                    be a list of already rendered neurons' actors] (default: {None})
            tracts {[list]} -- [list of tractography items, one per experiment] (default: {None})
            add_root {[bool]} -- [if true add semi transparent brain shape to scene. If None the default setting is used] (default: {None})

        """
        ABA.__init__(self)
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

        self.plotter = Plotter(axes=4, size=sz)
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

        self.rotated = False  # the first time the scene is rendered it must be rotated, the following times it must not be rotated
        self.inset = None  # the first time the scene is rendered create and store the inset here

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
        obj_path = os.path.join(folders_paths['models_fld'], "{}.obj".format(acronym))

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
    
    def get_region_CenterOfMass(self, regions, unilateral=True):
        """[Get the center of mass of the 3d mesh of  (or multiple) brain s. ]
        
        Arguments:
            regions {[str, list]} -- [string or list of string with acronym of brain regions of interest]
            unilateral {[bool]} -- [Get the CoM of the structure in just on hemisphere. Useful for lateralized structures like CA1. ] (default: {True})

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

    def get_n_rando_points_in_region(self, region):
        """
            npoints = 10

            scm, scs = self.actors['regions']['SCm'], self.actors['regions']['SCs']
            scm_bounds, scs_bounds = scm.bounds(), scs.bounds()
            bounds = [[np.min([scm_bounds[0], scs_bounds[0]]), np.min([scm_bounds[1], scs_bounds[1]])], 
                        [np.min([scm_bounds[2], scs_bounds[2]]), np.min([scm_bounds[3], scs_bounds[3]])], 
                        [np.min([scm_bounds[4], scs_bounds[4]]), np.min([scm_bounds[5], scs_bounds[5]])]]
        
            xmin = self.get_region_CenterOfMass('root', unilateral=False)[2]


            sc_points, niters = [], 0
            while len(sc_points) < npoints:
                x, y, z = np.random.randint(bounds[0][0], bounds[0][1]),  np.random.randint(bounds[1][0], bounds[1][1]),  np.random.randint(xmin = scene.get_region_CenterOfMass('root', unilateral=False)[2]
                , bounds[2][1])
                p = [x, y, z]
                if scm.isInside(p) or scs.isInside(p):
                    self.add_sphere_at_point(pos =p)
                    sc_points.append(p)
                niters += 1
        """
        raise NotImplementedError

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
    def add_from_file(self, filepath, name=None, **kwargs):
        actor = load_volume_file(filepath)
        self.actors['others'].append(actor)

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
            obj_file = os.path.join(folders_paths['models_fld'], "{}.obj".format(structure["acronym"]))
            
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
        if isinstance(neurons, str):
            if os.path.isfile(neurons):
                parser = NeuronsParser(scene=self, **kwargs)
                neurons, regions = parser.render_neurons(neurons)
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
            else:
                raise FileNotFoundError("The neuron file provided cannot be found: {}".format(neurons))
        elif isinstance(neurons, list):
            neurons = edit_neurons(neurons, **kwargs)
            self.actors["neurons"].extend(neurons)
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

    def add_streamlines(self, sl_file,  colorby = None, *args, **kwargs):
        """
        [Render streamline data downloaded from https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html]
        Arguments:
            sl_file {[str, list]} -- [Either a string to a JSON file with streamline data, or a list of json files.]
        
        Keyword Arguments:
            colorby {[str]} -- [Acronym of brain region to use to color the streamline data] (default: {None})
            
        """
        color = None
        if colorby is not None:
            try:
                color = self.structure_tree.get_structures_by_acronym([colorby])[0]['rgb_triplet']
                if "color" in kwargs.keys():
                    del kwargs["color"]
            except:
                raise ValueError("Could not extract color for region: {}".format(colorby))

        if isinstance(sl_file, list):
            if isinstance(sl_file[0], str): # we have a list of files to add
                for slf in tqdm(sl_file):
                    if color is not None:
                        streamlines = parse_streamline(slf, *args, color=color, **kwargs)
                    else:
                        streamlines = parse_streamline(slf, *args, **kwargs)

                    self.actors['tracts'].extend(streamlines)
            else:
                raise ValueError("unrecognized argument sl_file: {}".format(sl_file))
        else:
            if not isinstance(sl_file, str): raise ValueError("unrecognized argument sl_file: {}".format(sl_file))
            streamlines = parse_streamline(sl_file, *args,  **kwargs)
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

    def add_cells(self, coords, color="red", radius=25): # WIP 
        if isinstance(coords, pd.DataFrame):
            coords = [[x, y, z] for x,y,z in zip(coords['x'].values, coords['y'].values, coords['z'].values)]
        spheres = Spheres(coords, c=color, r=radius, res=3)
        self.actors['others'].append(spheres)

    ####### MANIPULATE SCENE
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

        if interactive and not video:
            show(*self.get_actors(), interactive=True, camera=self.camera_params, azimuth=azimuth, zoom=zoom)  
        elif video:
            show(*self.get_actors(), interactive=False, offscreen=True, camera=self.video_camera_params, azimuth=azimuth, zoom=2.5)  
        else:
            show(*self.get_actors(), interactive=False,  offscreen=True, camera=self.camera_params, azimuth=azimuth, zoom=zoom)  

    def _add_actors(self): # TODO fix this
        if self.plotter.renderer is None:
            return
        for actor in self.get_actors():
            self.plotter.renderer.AddActor(actor)


    ####### EXPORT SCENE
    def export(self, save_dir=None, savename="exported_scene", exportas="obj"):
        """[Exports the scene as a numpy file]
        
        Keyword Arguments:
            save_dir {[str]} -- [path to folder, if none default output folder is used] (default: {None})
            savename {str} -- [filename, can not include ".npy"] (default: {"exported_scene"})
        
        Raises:
            ValueError: [description]
        """
        if save_dir is None:
            save_dir = folders_paths['output_fld']
        
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
            save_dir = folders_paths['output_fld']
        
        if not os.path.isdir(save_dir):
            raise ValueError("Save folder not valid: {}".format(save_dir))

        curdir = os.getcwd()
        os.chdir(save_dir)
        exportWindow('{}.x3d'.format(filename))
        os.chdir(curdir)


class RatScene(Scene): # Subclass of Scene to override some methods for Rat data
    def __init__(self):
        Scene.__init__(self, add_root=False, display_inset=False)

        self.structures = get_rat_regions_metadata()
        self.structures_names = list(self.structures['Name'].values)

    def print_structures(self):
        ids, names = self.structures.Id.values, self.structures['Name'].values
        sort_idx = np.argsort(names)
        ids, names = ids[sort_idx], names[sort_idx]
        [print("(id: {}) - {}".format(a, n)) for a,n in zip(ids, names)]

    def add_brain_regions(self, brain_regions ,
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
                color = DEFAULT_STRUCTURE_COLOR
            elif isinstance(color, (list, tuple)):
                if not len(color) == len(brain_regions): 
                    raise ValueError("When passing a list of colors, the number of colors should be the same as the number of regions")
            else:
                color = [color for region in brain_regions]

            # loop over all brain regions
            for i, (col, region) in enumerate(zip(color, brain_regions)):
                # Load the object file as a mesh and store the actor
                self.actors["regions"][region] = get_rat_mesh_from_region(region, c=col, alpha=alpha)

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

    def render(self):
        mv = Plotter(N=self.N, axes=4, size="auto", sharecam=True)

        actors = []
        for i, scene in enumerate(self.scenes):
            scene_actors = scene.get_actors() 
            actors.append(scene_actors)
            mv.add(scene_actors)

        for i, scene_actors in enumerate(actors):
            mv.show(scene_actors, at=i,  interactive=False)
        interactive()


