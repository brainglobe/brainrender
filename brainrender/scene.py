import numpy as np
import os
import datetime
import random
from vtkplotter import Plotter, shapes, ProgressBar, show, settings, screenshot, importWindow, interactive
from vtkplotter.shapes import Cylinder, Line
from tqdm import tqdm
import pandas as pd
from functools import partial
from pathlib import Path
import datetime

from brainrender.colors import check_colors, get_n_shades_of, get_random_colors
from brainrender import * # Import default params 

from brainrender.Utils.ABA.connectome import ABA
from brainrender.Utils.data_io import load_volume_file
from brainrender.Utils.data_manipulation import get_coords, flatten_list, is_any_item_in_list, mirror_actor_at_point
from brainrender.Utils import actors_funcs

from brainrender.Utils.parsers.mouselight import NeuronsParser, edit_neurons
from brainrender.Utils.parsers.streamlines import parse_streamline

from brainrender.Utils.image import image_to_surface

from brainrender.Utils.camera import check_camera_param, set_camera


class Scene(ABA):  # subclass brain render to have acces to structure trees
    """
        The code below aims to create a scene to which actors can be added or removed, changed etc..
        It also facilitates the interaction with the scene (e.g. moving the camera) and the creation of
        snapshots or animated videos.
        The class Scene is based on the Plotter class of Vtkplotter: https://github.com/marcomusy/vtkplotter/blob/master/vtkplotter/plotter.py
        and other classes within the same package.
    """
    VIP_regions = DEFAULT_VIP_REGIONS
    VIP_color = DEFAULT_VIP_COLOR

    ignore_regions = ['retina', 'brain', 'fiber tracts', 'grey']

    def __init__(self,  brain_regions=None, 
                        regions_aba_color=False,
                        neurons=None, 
                        tracts=None, 
                        add_root=None, 
                        verbose=True, 
                        jupyter=False,
                        display_inset=None, 
                        base_dir=None,
                        camera=None, 
                        screenshot_kwargs = {},
                        **kwargs):
        """

            Creates and manages a Plotter instance

            :param brain_regions: list of brain regions acronyms to be added to the rendered scene (default value None)
            :param regions_aba_color: if True, use the Allen Brain Atlas regions colors (default value None)
            :param neurons: path to JSON or SWC file with data of neurons to be rendered [or list of files] (default value None)
            :param tracts: list of JSON files with tractography data to be rendered (default value None)
            :param add_root: if False a rendered outline of the whole brain is added to the scene (default value None)
            :param verbose: if False less feedback is printed to screen (default value True)
            :param jupyter: when using brainrender in Jupyter notebooks, this should be set to True (default value False)
            :param display_insert: if False the inset displaying the brain's outline is not rendered (but the root is added to the scene) (default value None)
            :param base_dir: path to directory to use for saving data (default value None)
            :param camera: name of the camera parameters setting to use (controls the orientation of the rendered scene)
            :param kwargs: can be used to pass path to individual data folders. See brainrender/Utils/paths_manager.py
            :param screenshot_kwargs: pass a dictionary with keys:
                        - 'folder' -> str, path to folder where to save screenshots
                        - 'name' -> str, filename to prepend to screenshots files
                        - 'format' -> str, 'png', 'svg' or 'jpg'
                        - scale -> float, values > 1 yield higher resultion screenshots
        """
        ABA.__init__(self, base_dir=base_dir, **kwargs)

        # Setup a few rendering options
        self.verbose = verbose
        self.regions_aba_color = regions_aba_color
        self.jupyter = jupyter

        if display_inset is None:
            self.display_inset = DISPLAY_INSET
        else:
            self.display_inset = display_inset

        if add_root is None:
            add_root = DISPLAY_ROOT

        # Camera parameters
        if camera is None:
            self.camera = CAMERA
        else:
            self.camera = check_camera_param(camera)

        # Set up vtkplotter plotter and actors records
        if WHOLE_SCREEN:
            sz = "full"
        else:
            sz = "auto"

        if SHOW_AXES:
            axes = 4
        else:
            axes = 0

        # Create plott and add function to capture keypresses
        self.plotter = Plotter(axes=axes, size=sz, pos=WINDOW_POS, bg=BACKGROUND_COLOR)

        self.screenshots_folder = screenshot_kwargs.pop('folder', DEFAULT_SCREENSHOT_FOLDER)
        self.screenshots_name = screenshot_kwargs.pop('name', DEFAULT_SCREENSHOT_NAME)
        self.screenshots_extension = screenshot_kwargs.pop('type', DEFAULT_SCREENSHOT_TYPE)
        self.screenshots_scale = screenshot_kwargs.pop('scale', DEFAULT_SCREENSHOT_SCALE)
        # self.plotter.keyPressFunction = self.keypress

        # Prepare store for actors added to scene
        self.actors = {"regions":{}, "tracts":[], "neurons":[], "root":None, "injection_sites":[], "others":[]}
        self._actors = None # store a copy of the actors when manipulations like slicing are done

        # Add items to scene
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

        # Placeholder variables
        self.inset = None  # the first time the scene is rendered create and store the inset here
        self.is_rendered = False # keep track of if the scene has already been rendered

    # ---------------------------------------------------------------------------- #
    #                                     Utils                                    #
    # ---------------------------------------------------------------------------- #

    # --------------------------- Check correct inputs --------------------------- #

    def check_obj_file(self, structure, obj_file):
        """
        If the .obj file for a brain region hasn't been downloaded already, this function downloads it and saves it.

        :param structure: string, acronym of brain region
        :param obj_file: path to .obj file to save downloaded data.

        """
        # checks if the obj file has been downloaded already, if not it takes care of downloading it
        if not os.path.isfile(obj_file):
            try:
                self.space.download_structure_mesh(structure_id = structure["id"],
                                                    ccf_version ="annotation/ccf_2017",
                                                    file_name=obj_file)
                return True
            except:
                print("Could not get mesh for: {}".format(obj_file))
                return False
        else: return True

    @staticmethod
    def check_region(region):
        """
        Check that the string passed is a valid brain region name.

        :param region: string, acronym of a brain region according to the Allen Brain Atlas.

        """
        if not isinstance(region, int) and not isinstance(region, str):
            raise ValueError("region must be a list, integer or string, not: {}".format(type(region)))
        else:
            return True

    # ------------------------------ ABA interaction ----------------------------- #
    def get_region_color(self, regions):
        """
        Gets the RGB color of a brain region from the Allen Brain Atlas.

        :param regions:  list of regions acronyms.

        """
        if not isinstance(regions, list):
            return self.structure_tree.get_structures_by_acronym([regions])[0]['rgb_triplet']
        else:
            return [self.structure_tree.get_structures_by_acronym([r])[0]['rgb_triplet'] for r in regions]

    def get_structure_parent(self, acronyms):
        """
        Gets the parent of a brain region (or list of regions) from the hierarchical structure of the
        Allen Brain Atals.

        :param acronyms: list of acronyms of brain regions.

        """
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
        """
        Gets the children of a brain region (or list of regions) from the hierarchical structure of the
        Allen Brain Atals.

        :param acronyms:  list of acronyms of brain regions.

        """
        raise NotImplementedError()

    def _get_structure_mesh(self, acronym, plotter=None,  **kwargs):
        """
        Fetches the mesh for a brain region from the ALlen Brain Atlas SDK.

        :param acronym: string, acronym of brain region
        :param plotter:  Optional. Use a vtk plotter different from the scene's default one (Default value = None)
        :param **kwargs:

        """
        if plotter is None:
            plotter = self.plotter

        structure = self.structure_tree.get_structures_by_acronym([acronym])[0]
        obj_path = os.path.join(self.mouse_meshes, "{}.obj".format(acronym))

        if self.check_obj_file(structure, obj_path):
            mesh = plotter.load(obj_path, **kwargs)
            return mesh
        else:
            return None

    # ----------------------------- Mesh interaction ----------------------------- #
    def get_region_CenterOfMass(self, regions, unilateral=True, hemisphere="right"):
        """
        Get the center of mass of the 3d mesh of one or multiple brain regions.

        :param regions: str, list of brain regions acronyms
        :param unilateral: bool, if True, the CoM is relative to one hemisphere (Default value = True)
        :param hemisphere: str, if unilteral=True, specifies which hemisphere to use ['left' or 'right'] (Default value = "right")
        :returns: coms = {list, dict} -- [if only one regions is passed, then just returns the CoM coordinates for that region.
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

    def get_n_rando_points_in_region(self, region, N):
        """
        Gets N random points inside (or on the surface) of the mesh defining a brain region.

        :param region: str, acronym of the brain region.
        :param N: int, number of points to return.

        """
        if region not in self.actors['regions']:
            raise ValueError("Region {} needs to be rendered first.".format(region))

        region_mesh = self.actors['regions'][region]
        region_bounds = region_mesh.bounds()

        X = np.random.randint(region_bounds[0], region_bounds[1], size=10000)
        Y = np.random.randint(region_bounds[2], region_bounds[3], size=10000)
        Z = np.random.randint(region_bounds[4], region_bounds[5], size=10000)
        pts = [[x, y, z] for x, y, z in zip(X, Y, Z)]

        ipts = region_mesh.insidePoints(pts)
        return random.choices(ipts, k=N)

    def get_region_unilateral(self, region, hemisphere="both", color=None, alpha=None):
        """
        Regions meshes are loaded with both hemispheres' meshes by default.
        This function splits them in two.

        :param region: str, actors of brain region
        :param hemisphere: str, which hemisphere to return ['left', 'right' or 'both'] (Default value = "both")
        :param color: color of each side's mesh. (Default value = None)
        :param alpha: transparency of each side's mesh.  (Default value = None)

        """
        if color is None: color = ROOT_COLOR
        if alpha is None: alpha = ROOT_ALPHA
        bilateralmesh = self._get_structure_mesh(region, c=color, alpha=alpha)


        com = bilateralmesh.centerOfMass()   # this will always give a point that is on the midline
        cut = bilateralmesh.cutWithPlane(origin=com, normal=(0, 0, 1))

        right = bilateralmesh.cutWithPlane( origin=com, normal=(0, 0, 1))
        
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
        """
        Handles the rendering of the inset showing the outline of the whole brain (root) in a corner of the scene.

        :param **kwargs:

        """
        if "plotter" in list(kwargs.keys()):
            self.add_root(render=False, **kwargs)

        if self.display_inset and self.inset is None:
            if self.root is None:
                self.add_root(render=False, **kwargs)
                self.inset = self.root.clone().scale(.5)
                self.root = None
                self.actors['root'] = None
            else:
                self.inset = self.root.clone().scale(.5)

            self.inset.alpha(1)
            self.plotter.showInset(self.inset, pos=(0.9,0.1))

    # ---------------------------- Actor interaction ----------------------------- #
    def edit_actors(self, actors, **kwargs):
        """
        edits a list of actors (e.g. render as wireframe or solid)
        :param actors: list of actors
        :param **kwargs:

        """
        if not isinstance(actors, list):
            actors = [actors]

        for actor in actors:
            actors_funcs.edit_actor(actor, **kwargs)



    # ---------------------------------------------------------------------------- #
    #                                POPULATE SCENE                                #
    # ---------------------------------------------------------------------------- #

    def add_vtkactor(self, actor):
        """
        Add a vtk actor to the scene

        :param actor:

        """
        self.actors['others'].append(actor)
        return actor

    def add_from_file(self, filepath, **kwargs):
        """
        Add data to the scene by loading them from a file. Should handle .obj, .vtk and .nii files.

        :param filepath: path to the file.
        :param **kwargs:

        """
        actor = load_volume_file(filepath, **kwargs)
        self.actors['others'].append(actor)
        return actor

    def add_root(self, render=True, **kwargs):
        """
        adds the root the scene

        :param render:  (Default value = True)
        :param **kwargs:

        """
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
                        colors=None, use_original_color=False, alpha=None, hemisphere=None, **kwargs):
        """
        Adds rendered brain regions with data from the Allen brain atlas. Many parameters can be passed to specify how the regions should be rendered.
        To treat a subset of the rendered regions, specify which regions are VIP. Use the kwargs to specify more detailes on how the regins should be rendered (e.g. wireframe look)

        :param brain_regions: str list of acronyms of brain regions
        :param VIP_regions: if a list of brain regions are passed, these are rendered differently compared to those in brain_regions (Default value = None)
        :param VIP_color: if passed, this color is used for the VIP regions (Default value = None)
        :param colors: str, color of rendered brian regions (Default value = None)
        :param use_original_color: bool, if True, the allen's default color for the region is used.  (Default value = False)
        :param alpha: float, transparency of the rendered brain regions (Default value = None)
        :param hemisphere: str (Default value = None)
        :param **kwargs:

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
            if isinstance(colors[0], (list, tuple)):
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
            try:
                structure = self.structure_tree.get_structures_by_acronym([region])[0]
            except Exception as e:
                raise ValueError(f'Could not find region with name {region}, got error: {e}')

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

            actors_funcs.edit_actor(obj, **kwargs)

            self.actors["regions"][region] = obj

    def add_neurons(self, neurons, display_soma_region=False, soma_regions_kwargs=None,
                    display_axon_regions=False,
                    display_dendrites_regions=False, **kwargs):
        """
        Adds rendered morphological data of neurons reconstructions downloaded from the Mouse Light project at Janelia (or other sources). Can accept rendered neurons
        or a list of files to be parsed for rendering. Several arguments can be passed to specify how the neurons are rendered.

        :param neurons: str, list, dict. File(s) with neurons data or list of rendered neurons.
        :param display_soma_region: if True, the region in which the neuron's soma is located is rendered (Default value = False)
        :param soma_regions_kwargs: dict, specifies how the soma regions should be rendered (Default value = None)
        :param display_axon_regions: if True, the regions through which the axons go through are rendered (Default value = False)
        :param display_dendrites_regions: if True, the regions through which the dendrites go through are rendered  (Default value = False)
        :param **kwargs:
        """
        def runfile(parser, neuron_file, soma_regions_kwargs):
            """

            :param parser:
            :param neuron_file:
            :param soma_regions_kwargs:

            """
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
            if not neurons:
                print("Didn't find any neuron to render.")
                return
            if not isinstance(neurons[0], str):
                neurons = edit_neurons(neurons, **kwargs)
                self.actors["neurons"].extend(neurons)
            else:
                # list of file paths
                if not os.path.isfile(neurons[0]): raise ValueError("Expected a list of file paths, got {} instead".format(neurons))
                parser = NeuronsParser(scene=self, **kwargs)

                print('\n')
                pb = ProgressBar(0, len(neurons), c="blue", ETA=1)
                for i in pb.range():
                    pb.print("Neuron {} of {}".format(i+1, len(neurons)))
                    runfile(parser, neurons[i], soma_regions_kwargs)
        else:
            if isinstance(neurons, dict):
                neurons = edit_neurons([neurons], **kwargs)
                self.actors["neurons"].extend(neurons)
            else:
                raise ValueError("the 'neurons' variable passed is neither a filepath nor a list of actors: {}".format(neurons))
        return neurons

    def edit_neurons(self, neurons=None, copy=False, **kwargs):

        """
        Edit neurons that have already been rendered. Change color, mirror them etc.

        :param neurons: list of neurons actors to edit, if None all neurons in the scene are edited (Default value = None)
        :param copy: if True, the neurons are copied first and then the copy is edited  (Default value = False)
        :param **kwargs:

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
                        VIP_regions=[], VIP_color=None, others_color="white", include_all_inj_regions=False,
                        extract_region_from_inj_coords=False, display_injection_volume=True):
        """
        Renders tractography data and adds it to the scene. A subset of tractography data can receive special treatment using the  with VIP regions argument:
        if the injection site for the tractography data is in a VIP regions, this is colored differently.

        :param tractography: list of dictionaries with tractography data
        :param color: color of rendered tractography data

        :param display_injection_structure: Bool, if True the injection structure is rendered (Default value = False)
        :param display_onlyVIP_injection_structure: bool if true displays the injection structure only for VIP regions (Default value = False)
        :param color_by: str, specifies which criteria to use to color the tractography (Default value = "manual")
        :param others_alpha: float (Default value = 1)
        :param verbose: bool (Default value = True)
        :param VIP_regions: list of brain regions with VIP treatement (Default value = [])
        :param VIP_color: str, color to use for VIP data (Default value = None)
        :param others_color: str, color for not VIP data (Default value = "white")
        :param include_all_inj_regions: bool (Default value = False)
        :param extract_region_from_inj_coords: bool (Default value = False)
        :param display_injection_volume: float, if True a spehere is added to display the injection coordinates and volume (Default value = True)
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

        if not isinstance(VIP_regions, list):
            raise ValueError("VIP_regions should be a list of acronyms")

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
            if VIP_color is not None:
                if not check_colors(VIP_color) or not check_colors(others_color):
                    raise ValueError("Invalid VIP or other color passed")
                try:
                    if include_all_inj_regions:
                        COLORS = [VIP_color if is_any_item_in_list( [x['abbreviation'] for x in t['injection-structures']], VIP_regions)\
                            else others_color for t in tractography]
                    else:
                        COLORS = [VIP_color if t['structure-abbrev'] in VIP_regions else others_color for t in tractography]
                except:
                    raise ValueError("Something went wrong while getting colors for tractography")
            else:
                COLORS = [self.get_region_color(t['structure-abbrev']) if t['structure-abbrev'] in VIP_regions else others_color for t in tractography]
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

            if alpha == 0:
                continue # skip transparent ones

            # check if we need to manually check injection coords
            if extract_region_from_inj_coords:
                try:
                    region = self.get_structure_from_coordinates(t['injection-coordinates'])
                    if region is None: continue
                    inj_structures = [self.get_structure_parent(region['acronym'])['acronym']]
                except:
                    raise ValueError(self.get_structure_from_coordinates(t['injection-coordinates']))
                if inj_structures is None: continue
                elif isinstance(extract_region_from_inj_coords, list):
                    # check if injection coord are in one of the brain regions in list, otherwise skip
                    if not is_any_item_in_list(inj_structures, extract_region_from_inj_coords):
                        continue

            # represent injection site as sphere
            if display_injection_volume:
                actors.append(shapes.Sphere(pos=t['injection-coordinates'],
                                c=color, r=INJECTION_VOLUME_SIZE*t['injection-volume'], alpha=TRACTO_ALPHA))

            points = [p['coord'] for p in t['path']]
            actors.append(shapes.Tube(points, r=TRACTO_RADIUS, c=color, alpha=alpha, res=TRACTO_RES))

        self.actors['tracts'].extend(actors)

    def add_streamlines(self, sl_file, *args, colorby=None, color_each=False,  **kwargs):
        """
        Render streamline data downloaded from https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html

        :param sl_file: path to JSON file with streamliens data [or list of files]
        :param colorby: str,  criteria for how to color the streamline data (Default value = None)
        :param color_each: bool, if True, the streamlines for each injection is colored differently (Default value = False)
        :param *args:
        :param **kwargs:

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
            if not isinstance(sl_file, (str, pd.DataFrame)):
                raise ValueError("unrecognized argument sl_file: {}".format(sl_file))
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
        """
        Creates Spherse at the location of injections with a volume proportional to the injected volume

        :param experiments: list of dictionaries with tractography data
        :param color:  (Default value = None)

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
            injection_sites.append(shapes.Sphere(pos=(exp["injection_x"], exp["injection_y"], exp["injection_z"]),
                    r = INJECTION_VOLUME_SIZE*exp["injection_volume"]*3,
                    c=color
                    ))

        self.actors['injection_sites'].extend(injection_sites)

    def add_sphere_at_point(self, pos=[0, 0, 0], radius=100, color="black", alpha=1, **kwargs):
        """
        Adds a shere at a location specified by the user

        :param pos: list of x,y,z coordinates (Default value = [0, 0, 0])
        :param radius: int, radius of the sphere (Default value = 100)
        :param color: color of the sphere (Default value = "black")
        :param alpha: transparency of the sphere (Default value = 1)
        :param **kwargs:
        """
        sphere = shapes.Sphere(pos=pos, r=radius, c=color, alpha=alpha, **kwargs)
        self.actors['others'].append(sphere)
        return sphere

    def add_cells_from_file(self, filepath, hdf_key=None, color="red",
                            radius=25, res=3, alpha=1):
        """
        Load location of cells from a file (csv and HDF) and render as spheres aligned to the root mesh.

        :param filepath: str path to file
        :param hdf_key: str (Default value = None)
        :param color: str, color of spheres used to render the cells (Default value = "red")
        :param radius: int, radius of spheres used to render the cells (Default value = 25)
        :param res: int, resolution of spheres used to render the cells (Default value = 3)
        :param alpha: float, transparency of spheres used to render the cells (Default value = 1)

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
            self.add_cells(cells, color=color, radius=radius, res=res,
                           alpha=alpha)

        elif filepath.suffix == ".pkl":
            cells = pd.read_picle(filepath)
            self.add_cells(cells, color=color, radius=radius, res=res,
                           alpha=alpha)
        else:
            raise NotImplementedError(
                f"File format: {filepath.suffix} is not currently supported. "
                f"Please use one of: {supported_formats}")

    def get_cells_in_region(self, cells, region):
        """
            Selects the cells that are in a list of user provided regions from a dataframe of cell locations

            :param cells: pd.DataFrame of cells x,y,z coordinates
        """
        if isinstance(region, list):
            region_list = []
            for reg in region:
                region_list.extend(list(self.get_structure_descendants(reg)['acronym'].values))
        else:
            region_list =  list(self.get_structure_descendants(region)['acronym'].values)
        return cells[cells.region.isin(region_list)]

    def add_cells(self, coords, color="red", color_by_region=False, radius=25, res=3, alpha=1, regions=None):
        """
        Renders cells given their coordinates as a collection of spheres.

        :param coords: pandas dataframe with x,y,z coordinates
        :param color: str, color of spheres used to render the cells (Default value = "red")
        :param radius: int, radius of spheres used to render the cells (Default value = 25)
        :param res: int, resolution of spheres used to render the cells (Default value = 3)
        :param alpha: float, transparency of spheres used to render the cells (Default value = 1)
        :param color_by_region: bool. If true the cells are colored according to the color of the brain region they are in
        :param regions: if a list of brain regions acronym is passed, only cells in these regions will be added to the scene

        """
        if isinstance(coords, pd.DataFrame):
            if regions is not None:
                coords = self.get_cells_in_region(coords, regions)
            coords = [[x, y, z] for x,y,z in zip(coords['x'].values, coords['y'].values, coords['z'].values)]
        else:
            raise ValueError("Unrecognized argument for cell coordinates")

        if color_by_region:
            regions = [self.get_structure_from_coordinates(p0) for p0 in coords]
            color = [list(np.float16(np.array(col)/255)) for col in self.get_region_color(regions)]

        spheres = shapes.Spheres(coords, c=color, r=radius, res=res, alpha=alpha)
        self.actors['others'].append(spheres)
        print("Added {} cells to the scene".format(len(coords)))

    def add_image(self, image_file_path, color=None, alpha=None,
                  obj_file_path=None, voxel_size=1, orientation="saggital",
                  invert_axes=None, extension=".obj", step_size=2,
                  keep_obj_file=True, overwrite='use', smooth=True):

        """
        Loads a 3d image and processes it to extract mesh coordinates. Mesh coordinates are extracted with
        a fast marching algorithm and saved to a .obj file. This file is then used to render the mesh.

        :param image_file_path: str
        :param color: str (Default value = None)
        :param alpha: int (Default value = None)
        :param obj_file_path: str (Default value = None)
        :param voxel_size: float (Default value = 1)
        :param orientation: str (Default value = "saggital")
        :param invert_axes: tuple (Default value = None)
        :param extension: str (Default value = ".obj")
        :param step_size: int (Default value = 2)
        :param keep_obj_file: bool (Default value = True)
        :param overwrite: str (Default value = 'use')
        :param overwrite: if a (Default value = 'use')
        :param smooth: bool (Default value = True)

        """

        # Check args
        if color is None: color = get_random_colors() # get a random color

        if alpha is None:
            alpha = DEFAULT_STRUCTURE_ALPHA

        if obj_file_path is None:
            obj_file_path = os.path.splitext(image_file_path)[0] + extension

        if os.path.exists(obj_file_path):
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
        else:
            print(f"Converting file: {image_file_path} to surface")
            image_to_surface(image_file_path, obj_file_path,
                             voxel_size=voxel_size,
                             orientation=orientation, invert_axes=invert_axes,
                             step_size=step_size)


        # render obj file, smooth and clean up.
        actor = self.add_from_file(obj_file_path, c=color, alpha=alpha)

        if smooth:
            actors_funcs.smooth_actor(actor)

        if not keep_obj_file:
            os.remove(obj_file_path)

    def add_optic_cannula(self, target_region=None, pos=None, x_offset=0, y_offset=0,
                z_offset=-500, use_line=False, **kwargs):
        """
            Adds a cylindrical vtk actor to scene to render optic cannulas. By default
            this is a semi-transparent blue cylinder centered on the center of mass of
            a specified target region and oriented vertically.

            :param target_region: str, acronym of target region to extract coordinates
                of implanted fiber. By defualt the fiber will be centered on the center
                of mass of the target region but the offset arguments can be used to
                fine tune the position. Alternative pass a 'pos' argument with XYZ coords.
            :param pos: list or tuple or np.array with X,Y,Z coordinates. Must have length = 3.
            :param x_offset, y_offset, z_offset: int, used to fine tune the coordinates of 
                the implanted cannula.
            :param **kwargs: used to specify which hemisphere the cannula is and parameters
                of the rendered cylinder: color, alpha, rotation axis...
        """
        # Set some default kwargs
        hemisphere = kwargs.pop('hemisphere', 'right')
        color = kwargs.pop('color', 'powderblue')
        radius = kwargs.pop('radius', 350)
        alpha = kwargs.pop('alpha', .5)
        
        # Get coordinates of brain-side face of optic cannula
        if target_region is not None:
            pos = self.get_region_CenterOfMass(target_region, unilateral=True, hemisphere=hemisphere)
        elif pos is None:
            print("No 'pos' or 'target_region' arguments were \
                            passed to 'add_optic_cannula', nothing to render")
            return
        else:
            if not len(pos) == 3:
                raise ValueError(f"Invalid target coordinates argument, pos: {pos}")

        # Offset position
        pos[0] += y_offset
        pos[1] += z_offset
        pos[2] += x_offset

        # Get coordinates of upper face
        bounds = self.root.bounds()
        top = pos.copy()
        top[1] = bounds[2] - 500

        if not use_line:
            cylinder = self.add_vtkactor(Cylinder(pos=[top, pos], c=color, r=radius, alpha=alpha, **kwargs))
        else:
            cylinder = self.add_vtkactor(Line(top, pos, c=color, alpha=alpha, lw=radius))
        return cylinder



    # ---------------------------------------------------------------------------- #
    #                                   RENDERING                                  #
    # ---------------------------------------------------------------------------- #
    # -------------------------------- Prep render ------------------------------- #

    def apply_render_style(self):
        actors = self.get_actors()

        for actor in actors:
            if actor is not None:
                if SHADER_STYLE != 'cartoon':
                    actor.lighting(style=SHADER_STYLE)
                else:
                    actor.lighting(style='plastic', 
                            enabled=False)

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

    # ---------------------------------- Render ---------------------------------- #
    def render(self, interactive=True, video=False, camera=None, **kwargs):
        """
        Takes care of rendering the scene
        """
        self.apply_render_style()

        if camera is None:
            camera = self.camera
        else:
            camera = check_camera_param(camera)
        set_camera(self, camera)

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
            show(*self.get_actors(), interactive=False, zoom=zoom)
        elif video:
            show(*self.get_actors(), interactive=False, offscreen=True, zoom=2.5)
        else:
            show(*self.get_actors(), interactive=False,  offscreen=True, zoom=zoom)

        if interactive and not video:
            show(*self.get_actors(), interactive=True)


    # ---------------------------------------------------------------------------- #
    #                               USER INTERACTION                               #
    # ---------------------------------------------------------------------------- #
    def keypress(self, key):
        if key == 's':
            if not os.path.isdir(self.screenshots_folder) and len(self.screenshots_folder):
                try:
                    os.mkdir(self.screenshots_folder)
                except Exception as e:
                    raise FileNotFoundError(f"Could not crate a folder to save screenshots.\n"+
                                f"Attempted to create a folder at {self.screenshots_folder}"+
                                f"But got exception: {e}")

            savename = os.path.join(self.screenshots_folder, self.screenshots_name)
            savename += f'_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'

            if '.' not in self.screenshots_extension:
                savename += f'.{self.screenshots_extension}'
            else:
                savename += self.screenshots_extension

            print(f'\nSaving screenshots at {savename}\n')
            screenshot(filename=savename, scale=self.screenshots_scale)

    def take_screenshot(self):
        self.keypress('s')





# ---------------------------------------------------------------------------- #
#                                 OTHER SCENES                                 #
# ---------------------------------------------------------------------------- #

class DualScene:
    """ """
    # A class that manages two scenes to display side by side
    def __init__(self, *args, **kwargs):
        self.scenes = [Scene( *args, **kwargs), Scene( *args, **kwargs)]

    def render(self):
        """ """

        self.apply_render_style()

        # Create camera and plotter
        if WHOLE_SCREEN: 
            sz = "full"
        else: 
            sz = "auto"
        
        if SHOW_AXES:
            axes = 4
        else:
            axes = 0

        mv = Plotter(N=2, axes=axes, size=sz, pos=WINDOW_POS, bg=BACKGROUND_COLOR, sharecam=True)

        actors = []
        for scene in self.scenes:
            scene_actors = scene.get_actors()
            actors.append(scene_actors)
            mv.add(scene_actors)

        mv.show(actors[0], at=0, zoom=1.15, axes=axes, roll=180,  interactive=False)    
        mv.show(actors[1], at=1,  interactive=False)
        interactive()


class MultiScene:
    """ """
    def __init__(self, N,  *args, **kwargs):
        self.scenes = [Scene( *args, **kwargs) for i in range(N)]
        self.N = N

    def render(self, _interactive=True,  **kwargs):
        """

        :param _interactive:  (Default value = True)
        :param **kwargs:

        """

        self.apply_render_style()

        if self.N > 4:
            print("Rendering {} scenes. Might take a few minutes.".format(self.N))
        mv = Plotter(N=self.N, axes=4, size="auto", sharecam=True, bg=BACKGROUND_COLOR)

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


