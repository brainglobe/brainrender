import numpy as np
import os
from vtkplotter import *
import copy

from BrainRender.Utils.data_io import load_json
from BrainRender.Utils.data_manipulation import get_coords, flatten_list, get_slice_coord
from BrainRender.colors import *
from BrainRender.variables import *
from BrainRender.ABA_analyzer import ABA
from BrainRender.Utils.mouselight_parser import render_neurons, edit_neurons
from BrainRender.settings import *

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

    ignore_regions = ['retina']


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
            self.add_root()
        else:
            self.root = None

        self.rotated = False  # the first time the scene is rendered it must be rotated, the following times it must not be rotated
        self.inset = None  # the first time the scene is rendered create and store the inset here

    ####### UTILS
    def check_obj_file(self, structure, obj_file):
        # checks if the obj file has been downloaded already, if not it takes care of downloading it
        if not os.path.isfile(obj_file):
            try:
                mesh = self.space.download_structure_mesh(structure_id = structure[0]["id"], 
                                                ccf_version ="annotation/ccf_2017", 
                                                file_name=obj_file)
            except:
                raise ValueError("Could not get mesh for: {}".format(obj_file))

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

    def _get_structure_mesh(self, acronym, **kwargs):
        structure = self.structure_tree.get_structures_by_acronym([acronym])[0]
        obj_path = os.path.join(folders_paths['models_fld'], "{}.obj".format(acronym))
        self.check_obj_file(structure, obj_path)

        mesh = self.plotter.load(obj_path, **kwargs)
        return mesh

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

    def get_region_unilateral(self, region, hemisphere="both"):
        """[Regions meshes are loaded with both hemispheres' meshes. This function splits them in two. ]
        
        Arguments:
            region {[str]} -- [acronym of the brain region]
            hemisphere {[str]} -- [which hemispheres to return, options are "left", "right", and "both"]

        """
        bilateralmesh = self._get_structure_mesh(region, c=ROOT_COLOR, alpha=ROOT_ALPHA)

        
        com = bilateralmesh.centerOfMass()   # this will always give a point that is on the midline
        cut = bilateralmesh.cutWithPlane(showcut=True, origin=com, normal=(0, 0, 1))

        right = bilateralmesh.cutWithPlane(showcut=False, origin=com, normal=(0, 0, 1))
        left = bilateralmesh.cutWithPlane(showcut=False, origin=com, normal=(0, 0, 1))

        if hemisphere == "both":
            return left, right
        elif hemisphere == "left":
            return left
        else:
            return right

    ###### ADD  and EDIT ACTORS TO SCENE

    def add_root(self, render=True):
        if not render:
            self.root = self._get_structure_mesh('root', c=ROOT_COLOR, alpha=0)
        else:
            self.root = self._get_structure_mesh('root', c=ROOT_COLOR, alpha=ROOT_ALPHA)

        self.root.pickable(value=False)

        # get the center of the root and the bounding box
        self.root_center = self.root.centerOfMass()
        self.root_bounds = {"x":self.root.xbounds(), "y":self.root.ybounds(), "z":self.root.zbounds()}

        if render:
            self.actors['root'] = self.root

    def add_brain_regions(self, brain_regions, VIP_regions=None, VIP_color=None, 
                        colors=None, use_original_color=False, alpha=None): 
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
            if region in self.ignore_regions: continue
            self.check_region(region)

            # if it's an ID get the acronym
            if isinstance(region, int):
                region = self.structure_tree.get_region_by_id([region])[0]['acronym']

            if self.verbose: print("Rendering: ({})".format(region))
            
            # get the structure and check if we need to download the object file
            structure = self.structure_tree.get_structures_by_acronym([region])[0]
            obj_file = os.path.join(folders_paths['models_fld'], "{}.obj".format(structure["acronym"]))
            self.check_obj_file(structure, obj_file)

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
            self.actors["regions"][region] = self.plotter.load(obj_file, c=color, 
                                                                        alpha=alpha) 

    def add_neurons(self, neurons, **kwargs):
        if isinstance(neurons, str):
            if os.path.isfile(neurons):
                self.actors["neurons"].extend(render_neurons(neurons, **kwargs))
            else:
                raise FileNotFoundError("The neurons JSON file provided cannot be found: {}".format(neurons))
        elif isinstance(neurons, list):
            neurons = edit_neurons(neurons, **kwargs)
            self.actors["neurons"].extend(neurons)
        else:
            raise ValueError("the 'neurons' variable passed is neither a filepath nor a list of actors: {}".format(neurons))

    def edit_neurons(self, **kwargs):
        """
            Edit already rendered neurons 
        """
        neurons = self.actors["neurons"]
        self.actors["neurons"] = []
        self.actors["neurons"] = edit_neurons(neurons, **kwargs)

    def add_tractography(self, tractography, color=None, display_injection_structure=False, display_onlyVIP_injection_structure=False, color_by="manual", 
                        VIP_regions=[], VIP_color="red", others_color="white"):
        """
            Color can be either None (in which case default is used), a single color (e.g. "red") or 
            a list of colors, in which case each tractography tract will have the corresponding color

            display_injection_structure: display the brain region in which the injection was made
            display_onlyVIP_injection_structure: if True and display_injection_structure == True then only the brian structures that are in VIP_regions are displayed
            color_by: [str] specify how to color tracts and, if displayed, injection structures.
                    options are:
                        - manual: use the value of 'color'
                        - region: color by the ABA RGB color of injection region
                        - target_region: color tracts and regions in VIP_regions with VIP_coor and others with others_color
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
                COLORS = [VIP_color if t['structure-abbrev'] in VIP_regions else others_color for t in tractography]
            except:
                raise ValueError("Something went wrong while getting colors for tractography")
        else:
            raise ValueError("Unrecognised 'color_by' argument {}".format(color_by))
        # add actors to represent tractography data
        actors = []
        for i, (t, color) in enumerate(zip(tractography, COLORS)):
            # represent injection site as sphere
            actors.append(Sphere(pos=t['injection-coordinates'], c=color, r=INJECTION_VOLUME_SIZE*t['injection-volume'], alpha=TRACTO_ALPHA))

            # show brain structures in which injections happened
            if display_injection_structure:
                if t['structure-abbrev'] not in list(self.actors['regions'].keys()):
                    if display_onlyVIP_injection_structure and t['structure-abbrev'] in VIP_regions:
                        self.add_brain_regions([t['structure-abbrev']], colors=color)
                    elif not display_onlyVIP_injection_structure:
                        self.add_brain_regions([t['structure-abbrev']], colors=color)


            # get tractography points and represent as list
            points = [p['coord'] for p in t['path']]
            actors.append(shapes.Tube(points, r=TRACTO_RADIUS, c=color, alpha=TRACTO_ALPHA, res=TRACTO_RES))

        self.actors['tracts'].extend(actors)

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

    ####### MANIPULATE SCENE
    def Slice(self, axis="x", j=0, onlyroot=False, close_holes=False):
        """
            x -> coronal
            y -> horizontal
            z -> sagittal

            # values of J should be in range 0, 1
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

                # raise ValueError(self.root_center, self.root_bounds, pos)

                actor = actor.cutWithPlane(origin=pos, normal=normal)


    
            

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

        if self.display_inset and self.inset is None:
            if self.root is None:
                self.add_root(render=False)

            self.inset = self.root.clone().scale(.5)
            self.inset.alpha(1)
            self.plotter.showInset(self.inset, pos=(0.9,0.2))  

            self.root = None
            self.actors['root'] = None

        if VERBOSE and not self.jupyter:
            print(INTERACTIVE_MSG)
        elif self.jupyter:
            print("\n\npress 'Esc' to Quit")
        else:
            print("\n\npress 'q' to Quit")

        if WHOLE_SCREEN:
            zoom = 1.5
        else:
            zoom = 1.25

        if interactive and not video:
            show(*self.get_actors(), interactive=True, camera=self.camera_params, azimuth=azimuth, zoom=zoom)  
        elif video:
            show(*self.get_actors(), interactive=False,  offscreen=True, camera=self.video_camera_params, azimuth=azimuth, zoom=zoom)  
        else:
            show(*self.get_actors(), interactive=False,  offscreen=True, camera=self.camera_params, azimuth=azimuth, zoom=zoom)  

    ####### EXPORT SCENE
    def export_scene(self, merge_actors=True, filename='scene.vtk'):
        actors = self.get_actors()

        if merge_actors:
            scene = merge(*actors)

        save(scene, os.path.join(rendered_scenes, filename))
        # scene.write(os.path.join(rendered_scenes, filename))
        # exportWindow(actors, os.path.join(rendered_scenes, filename))


if __name__ == "__main__":
    # get vars to populate test scene
    br = ABA()

    tract = br.get_projection_tracts_to_target("PRNr")


    # makes cene
    scene = Scene(tracts=tract)
    scene.add_brain_regions(["PRNr", "PRNc"], VIP_color="red", VIP_regions=["PRNr", "PRNc"])

    afferents = br.analyze_afferents("PRNc")
    scene.add_brain_regions([a for a in afferents.acronym.values[-10:] if a not in ["PRNc", "PRNr"]])

    tract = br.get_projection_tracts_to_target("PRNc")
    scene.add_tractography(tract, color="r")

    afferents = br.analyze_afferents("PRNr")
    scene.add_brain_regions([a for a in afferents.acronym.values[-10:] if a not in ["PRNc", "PRNr"]])
    # scene.add_injection_sites(experiments)


    scene.render()