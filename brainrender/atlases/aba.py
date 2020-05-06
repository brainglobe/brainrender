import pandas as pd
import numpy as np
import os
from tqdm import tqdm

from vtkplotter import ProgressBar, shapes, merge
from vtkplotter.mesh import Mesh as Actor

from brainrender.Utils.data_io import load_mesh_from_file, load_json
from brainrender.Utils.data_manipulation import get_coords, flatten_list, is_any_item_in_list
from brainrender.Utils.parsers.mouselight import NeuronsParser, edit_neurons
from brainrender.Utils.parsers.streamlines import parse_streamline
from brainrender import STREAMLINES_RESOLUTION, INJECTION_VOLUME_SIZE
from brainrender.Utils.webqueries import request
from brainrender import * # Import default params 
from brainrender.Utils import actors_funcs


from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
from allensdk.api.queries.ontologies_api import OntologiesApi
from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
from allensdk.api.queries.tree_search_api import TreeSearchApi
from allensdk.core.reference_space_cache import ReferenceSpaceCache

from brainrender.atlases.base import Atlas


class ABA(Atlas):
    """
    This class handles interaction with the Allen Brain Atlas datasets and APIs to get structure trees,
    experimental metadata and results, tractography data etc. 
    """
    # useful vars for analysis    
    excluded_regions = ["fiber tracts"]
    resolution = 25

    _root_bounds = [[-17, 13193], 
                   [ 134, 7564], 
                    [486, 10891]]

    _root_midpoint = [np.mean([-17, 13193]), 
                        np.mean([134, 7564]),
                        np.mean([486, 10891])]

    atlas_name = "ABA"
    mesh_format = 'obj'

    base_url = "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_NNN.json.gz"
    # Used for streamlines

    def __init__(self, projection_metric = "projection_energy", base_dir=None, **kwargs):
        """ 
        Set up file paths and Allen SDKs
        
        :param base_dir: path to directory to use for saving data (default value None)
        :param path_fiprojection_metricle: - str, metric to quantify the strength of projections from the Allen Connectome. (default value 'projection_energy')
        :param kwargs: can be used to pass path to individual data folders. See brainrender/Utils/paths_manager.py

        """

        Atlas.__init__(self, base_dir=base_dir, **kwargs)
        self.meshes_folder = self.mouse_meshes # where the .obj mesh for each region is saved

        self.projection_metric = projection_metric

        # get mouse connectivity cache and structure tree
        self.mcc = MouseConnectivityCache(manifest_file=os.path.join(self.mouse_connectivity_cache, "manifest.json"))
        self.structure_tree = self.mcc.get_structure_tree()
        
        # get ontologies API and brain structures sets
        self.oapi = OntologiesApi()
        self.get_structures_sets()

        # get reference space
        self.space = ReferenceSpaceApi()
        self.spacecache = ReferenceSpaceCache(
            manifest=os.path.join(self.annotated_volume_fld, "manifest.json"),  # downloaded files are stored relative to here
            resolution=self.resolution,
            reference_space_key="annotation/ccf_2017"  # use the latest version of the CCF
            )
        self.annotated_volume, _ = self.spacecache.get_annotation_volume()

        # mouse connectivity API [used for tractography]
        self.mca = MouseConnectivityApi()

        # Get tree search api
        self.tree_search = TreeSearchApi()

        # Get some metadata about experiments
        self.all_experiments = self.mcc.get_experiments(dataframe=True)
        self.strains = sorted([x for x in set(self.all_experiments.strain) if x is not None])
        self.transgenic_lines = sorted(set([x for x in set(self.all_experiments.transgenic_line) if x is not None]))


        # Store all regions metadata
        self.regions = self.other_sets["Structures whose surfaces are represented by a precomputed mesh"].sort_values('acronym')
        self.region_acronyms = list(self.other_sets["Structures whose surfaces are represented by a precomputed mesh"].sort_values(
                                            'acronym').acronym.values)

    # ---------------------------------------------------------------------------- #
    #                       Methods to support Scene creation                      #
    # ---------------------------------------------------------------------------- #
    """
        These methods are used by brainrender.scene to populate a scene using
        the Allen brain atlas meshes. They overwrite methods of the base atlas class
    """

    # ---------------------- Overwriting base atlas methods ---------------------- #
    def _check_obj_file(self, region, obj_file):
        """
        If the .obj file for a brain region hasn't been downloaded already, this function downloads it and saves it.

        :param region: string, acronym of brain region
        :param obj_file: path to .obj file to save downloaded data.

        """
        # checks if the obj file has been downloaded already, if not it takes care of downloading it
        if not os.path.isfile(obj_file):
            try:
                structure = self.structure_tree.get_structures_by_acronym([region])[0]
            except Exception as e:
                raise ValueError(f'Could not find region with name {region}, got error: {e}')

            try:
                self.space.download_structure_mesh(structure_id = structure["id"],
                                                    ccf_version ="annotation/ccf_2017",
                                                    file_name=obj_file)
                return True
            except:
                print("Could not get mesh for: {}".format(obj_file))
                return False
        else: return True

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
            # Check if input is an actor or if we need to load one
            if isinstance(regions, Actor):
                mesh = regions
            else:
                # load mesh corresponding to brain region
                if unilateral:
                    mesh = self.get_region_unilateral(regions, hemisphere="left")
                else:
                    mesh = self._get_structure_mesh(regions)

            #  Check if we are considering only one hemisphere
            if unilateral and hemisphere.lower() == 'right':
                if self.root is None:
                    self.add_root(render=False)
                return list(np.array(get_coords([np.int(x) for x in mesh.centerOfMass()], 
                                        mirror=self.root_center[2])).astype(np.int32))
            else:
                return [np.int(x) for x in mesh.centerOfMass()]
        else:
            coms = {}
            for region in regions:
                if isinstance(region, Actor):
                    mesh = region
                else:
                    if unilateral:
                        mesh = self.get_region_unilateral(region, hemisphere="left")
                    else:
                        mesh = self._get_structure_mesh(region)
                coms[region] = [np.int(x) for x in mesh.centerOfMass()]
            return coms

    def _get_structure_mesh(self, acronym,   **kwargs):
        """
        Fetches the mesh for a brain region from the Allen Brain Atlas SDK.

        :param acronym: string, acronym of brain region
        :param **kwargs:

        """
        structure = self.structure_tree.get_structures_by_acronym([acronym])[0]
        obj_path = os.path.join(self.mouse_meshes, "{}.obj".format(acronym))

        if self._check_obj_file(structure, obj_path):
            mesh = load_mesh_from_file(obj_path, **kwargs)
            return mesh
        else:
            return None

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
        left = actors_funcs.mirror_actor_at_point(right.clone(), com, axis='x')

        if hemisphere == "both":
            return left, right
        elif hemisphere == "left": 
            return left 
        else:
            return right

    @staticmethod # static method because this should inherit from scene
    def add_neurons(self, neurons, display_soma_region=False, soma_regions_kwargs=None,
                    display_axon_regions=False,
                    display_dendrites_regions=False, 
                    **kwargs):
        """
        Adds rendered morphological data of neurons reconstructions downloaded from the Mouse Light project at Janelia (or other sources). Can accept rendered neurons
        or a list of files to be parsed for rendering. Several arguments can be passed to specify how the neurons are rendered.

        :param scene: instance of brainrender Scene to use to render neurons
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
                scene.add_brain_regions(flatten_list([r['soma'] for r in regions]), **soma_regions_kwargs)
            if display_axon_regions:
                scene.add_brain_regions(flatten_list([r['axon'] for r in regions]), **soma_regions_kwargs)
            if display_dendrites_regions:
                scene.add_brain_regions(flatten_list([r['dendrites'] for r in regions]), **soma_regions_kwargs)

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
        return  

    # -------------------------- Methods specific to ABA ------------------------- #

    @staticmethod
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
            COLORS = [self.atlas.get_region_color(t['structure-abbrev']) for t in tractography]

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
                COLORS = [self.atlas.get_region_color(t['structure-abbrev']) if t['structure-abbrev'] in VIP_regions else others_color for t in tractography]
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
                inj_structures = [self.atlas.get_structure_parent(t['structure-abbrev'])['acronym']]

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
                    region = self.atlas.get_structure_from_coordinates(t['injection-coordinates'], 
                                                            just_acronym=False)
                    if region is None: continue
                    inj_structures = [self.atlas.get_structure_parent(region['acronym'])['acronym']]
                except:
                    raise ValueError(self.atlas.get_structure_from_coordinates(t['injection-coordinates'], 
                                                            just_acronym=False))
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

    @staticmethod
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

    @staticmethod
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


    # ---------------------------------------------------------------------------- #
    #                          STRUCTURE TREE INTERACTION                          #
    # ---------------------------------------------------------------------------- #

    # ------------------------- Get/Print structures sets ------------------------ #

    def get_structures_sets(self):
        """ 
        Get the Allen's structure sets.
        """
        summary_structures = self.structure_tree.get_structures_by_set_id([167587189])  # main summary structures
        summary_structures = [s for s in summary_structures if s["acronym"] not in self.excluded_regions]
        self.structures = pd.DataFrame(summary_structures)

        # Other structures sets
        try:
            all_sets = pd.DataFrame(self.oapi.get_structure_sets())
        except:
            print("Could not retrieve data, possibly because there is no internet connection.")
        else:
            sets = ["Summary structures of the pons", "Summary structures of the thalamus", 
                        "Summary structures of the hypothalamus", "List of structures for ABA Fine Structure Search",
                        "Structures representing the major divisions of the mouse brain", "Summary structures of the midbrain", "Structures whose surfaces are represented by a precomputed mesh"]
            self.other_sets = {}
            for set_name in sets:
                set_id = all_sets.loc[all_sets.description == set_name].id.values[0]
                self.other_sets[set_name] = pd.DataFrame(self.structure_tree.get_structures_by_set_id([set_id]))

            self.all_avaliable_meshes = sorted(self.other_sets["Structures whose surfaces are represented by a precomputed mesh"].acronym.values)

    def print_structures_list_to_text(self):
        """ 
        Saves the name of every brain structure for which a 3d mesh (.obj file) is available in a text file.
        """
        s = self.other_sets["Structures whose surfaces are represented by a precomputed mesh"].sort_values('acronym')
        with open('all_regions.txt', 'w') as o:
            for acr, name in zip(s.acronym.values, s['name'].values):
                o.write("({}) -- {}\n".format(acr, name))

    def print_structures(self):
        """ 
        Prints the name of every structure in the structure tree to the console.
        """
        acronyms, names = self.structures.acronym.values, self.structures['name'].values
        sort_idx = np.argsort(acronyms)
        acronyms, names = acronyms[sort_idx], names[sort_idx]
        [print("({}) - {}".format(a, n)) for a,n in zip(acronyms, names)]

    # -------------------------- Parents and descendants ------------------------- #
    def get_structure_ancestors(self, regions, ancestors=True, descendants=False):
        """
        Get's the ancestors of the region(s) passed as arguments

        :param regions: str, list of str with acronums of regions of interest
        :param ancestors: if True, returns the ancestors of the region  (Default value = True)
        :param descendants: if True, returns the descendants of the region (Default value = False)

        """

        if not isinstance(regions, list):
            struct_id = self.structure_tree.get_structures_by_acronym([regions])[0]['id']
            return pd.DataFrame(self.tree_search.get_tree('Structure', struct_id, ancestors=ancestors, descendants=descendants))
        else:
            ancestors = []
            for region in regions:
                struct_id = self.structure_tree.get_structures_by_acronym([region])[0]['id']
                ancestors.append(pd.DataFrame(self.tree_search.get_tree('Structure', struct_id, ancestors=ancestors, descendants=descendants)))
            return ancestors

    def get_structure_descendants(self, regions):
        return self.get_structure_ancestors(regions, ancestors=False, descendants=True)

    def get_structure_parent(self, acronyms):
        """
        Gets the parent of a brain region (or list of regions) from the hierarchical structure of the
        Allen Brain Atals.

        :param acronyms: list of acronyms of brain regions.

        """
        if not isinstance(acronyms, list):
            self._check_valid_region_arg(acronyms)
            s = self.structure_tree.get_structures_by_acronym([acronyms])[0]
            if s['id'] in self.structures.id.values:
                return s
            else:
                return self.get_structure_ancestors(s['acronym']).iloc[-1]
        else:
            parents = []
            for region in acronyms:
                self._check_valid_region_arg(region)
                s = self.structure_tree.get_structures_by_acronym(acronyms)[0]

                if s['id'] in self.structures.id.values:
                    parents.append(s)
                parents.append(self.get_structure_ancestors(s['acronym']).iloc[-1])
            return parents

    # ----------------------------------- Utils ---------------------------------- #
    def get_region_color(self, regions):
        """
        Gets the RGB color of a brain region from the Allen Brain Atlas.

        :param regions:  list of regions acronyms.

        """
        if not isinstance(regions, list):
            return self.structure_tree.get_structures_by_acronym([regions])[0]['rgb_triplet']
        else:
            return [self.structure_tree.get_structures_by_acronym([r])[0]['rgb_triplet'] for r in regions]

    @staticmethod
    def _check_valid_region_arg(region):
        """
        Check that the string passed is a valid brain region name.

        :param region: string, acronym of a brain region according to the Allen Brain Atlas.

        """
        if not isinstance(region, int) and not isinstance(region, str):
            raise ValueError("region must be a list, integer or string, not: {}".format(type(region)))
        else:
            return True

    def get_hemispere_from_point(self, p0):
        if p0[2] > self._root_midpoint[2]:
            return 'right'
        else:
            return 'left'

    def get_structure_from_coordinates(self, p0, just_acronym=True):
        """
        Given a point in the Allen Mouse Brain reference space, returns the brain region that the point is in. 

        :param p0: list of floats with XYZ coordinates. 

        """
        voxel = np.round(np.array(p0) / self.resolution).astype(int)
        try:
            structure_id = self.annotated_volume[voxel[0], voxel[1], voxel[2]]
        except:
            return None

        # Each voxel in the annotation volume is annotated as specifically as possible
        structure = self.structure_tree.get_structures_by_id([structure_id])[0]
        if structure is not None:
            if just_acronym:
                return structure['acronym']
        return structure
    
    def get_colors_from_coordinates(self, p0):
        """
            Given a point or a list of points returns a list of colors where 
            each item is the color of the brain region each point is in
        """
        if isinstance(p0[0], (float, int)):
            struct = self.get_structure_from_coordinates(p0, just_acronym=False)
            if struct is not None:
                return struct['rgb_triplet']
            else:
                return None
        else:
            structures = [self.get_structure_from_coordinates(p, just_acronym=False) for p in p0]
            colors = [struct['rgb_triplet'] if struct is not None else None 
                            for struct in structures]
            return colors 


    # ---------------------------------------------------------------------------- #
    #                       CONNECTOME EXPERIMENT INTERACTION                      #
    # ---------------------------------------------------------------------------- #

    def load_all_experiments(self, cre=False):
        """
        This function downloads all the experimental data from the MouseConnectivityCache and saves the unionized results
        as pickled pandas dataframes. The process is slow, but the ammount of disk space necessary to save the data is small,
        so it's worth downloading all the experiments at once to speed up subsequent analysis.

        :param cre: Bool - data from either wild time or cre mice lines (Default value = False)

        """
        
        if not cre: raise NotImplementedError("Only works for wild type sorry")
        # Downloads all experiments from allen brain atlas and saves the results as an easy to read pkl file
        for acronym in self.structures.acronym.values:
            print("Fetching experiments for : {}".format(acronym))

            structure = self.structure_tree.get_structures_by_acronym([acronym])[0]
            experiments = self.mcc.get_experiments(cre=cre, injection_structure_ids=[structure['id']])

            print("     found {} experiments".format(len(experiments)))

            try:
                structure_unionizes = self.mcc.get_structure_unionizes([e['id'] for e in experiments], 
                                                            is_injection=False,
                                                            structure_ids=self.structures.id.values,
                                                            include_descendants=False)
            except: pass
            structure_unionizes.to_pickle(os.path.join(self.output_data, "{}.pkl".format(acronym)))
    
    def experiments_source_search(self, SOI, *args, source=True,  **kwargs):
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

        return pd.DataFrame(self.mca.experiment_source_search(injection_structures=injection_structures,
                                            target_domain = target_domain,
                                            transgenic_lines=transgenic_id,
                                            primary_structure_only=primary_structure_only))

    def experiments_target_search(self, *args, **kwargs):
        """

        :param *args: 
        :param **kwargs: 

        """
        return self.experiments_source_search(*args, source=False, **kwargs)

    def fetch_experiments_data(self, experiments_id, *args, average_experiments=False, **kwargs):
        """
        Get data and metadata for expeirments in the Allen Mouse Connectome project. 
    
        :param experiments_id: int, list, np.ndarray with ID of experiments whose data need to be fetched
        :param *args: 
        :param average_experiments:  (Default value = False)
        :param **kwargs: 

        """
        if isinstance(experiments_id, np.ndarray):
            experiments_id = [int(x) for x in experiments_id]
        elif not isinstance(experiments_id, list): 
            experiments_id = [experiments_id]
        if [x for x in experiments_id if not isinstance(x, int)]:
            raise ValueError("Invalid experiments_id argument: {}".format(experiments_id))

        default_structures_ids = self.structures.id.values


        is_injection = kwargs.pop('is_injection', False) # Include only structures that are not injection
        structure_ids = kwargs.pop('structure_ids', default_structures_ids) # Pass IDs of structures of interest 
        hemisphere_ids= kwargs.pop('hemisphere_ids', None) # 1 left, 2 right, 3 both

        if not average_experiments:
            return pd.DataFrame(self.mca.get_structure_unionizes(experiments_id,
                                                is_injection = is_injection,
                                                structure_ids = structure_ids,
                                                hemisphere_ids = hemisphere_ids))
        else:
            raise NotImplementedError("Need to find a way to average across experiments")
            unionized = pd.DataFrame(self.mca.get_structure_unionizes(experiments_id,
                                                is_injection = is_injection,
                                                structure_ids = structure_ids,
                                                hemisphere_ids = hemisphere_ids))

        for regionid in list(set(unionized.structure_id)):
            region_avg = unionized.loc[unionized.structure_id == regionid].mean(axis=1) ## UNUSED!!??

    ####### ANALYSIS ON EXPERIMENTAL DATA
    def analyze_efferents(self, ROI, projection_metric = None):
        """
        Loads the experiments on ROI and looks at average statistics of efferent projections

        :param ROI: str, acronym of brain region of interest
        :param projection_metric: if None, the default projection metric is used, otherwise pass a string with metric to use (Default value = None)

        """
        if projection_metric is None: 
            projection_metric = self.projection_metric

        experiment_data = pd.read_pickle(os.path.join(self.output_data, "{}.pkl".format(ROI)))
        experiment_data = experiment_data.loc[experiment_data.volume > self.volume_threshold]

        # Loop over all structures and get the injection density
        results = {"left":[], "right":[], "both":[], "id":[], "acronym":[], "name":[]}
        for target in self.structures.id.values:
            target_acronym = self.structures.loc[self.structures.id == target].acronym.values[0]
            target_name = self.structures.loc[self.structures.id == target].name.values[0]

            exp_target = experiment_data.loc[experiment_data.structure_id == target]

            exp_target_hemi = self.hemispheres(exp_target.loc[exp_target.hemisphere_id == 1], 
                                                exp_target.loc[exp_target.hemisphere_id == 2], 
                                                exp_target.loc[exp_target.hemisphere_id == 3])
            proj_energy = self.hemispheres(np.nanmean(exp_target_hemi.left[projection_metric].values),
                                            np.nanmean(exp_target_hemi.right[projection_metric].values),
                                            np.nanmean(exp_target_hemi.both[projection_metric].values)
            )


            for hemi in self.hemispheres_names:
                results[hemi].append(proj_energy._asdict()[hemi])
            results["id"].append(target)
            results["acronym"].append(target_acronym)
            results["name"].append(target_name)

        results = pd.DataFrame.from_dict(results).sort_values("right", na_position = "first")
        return results

    def analyze_afferents(self, ROI, projection_metric = None):
        """[Loads the experiments on ROI and looks at average statistics of afferent projections]

        :param ROI: str, acronym of region of itnerest
        :param projection_metric: if None, the default projection metric is used, otherwise pass a string with metric to use (Default value = None)

        """
        if projection_metric is None: 
            projection_metric = self.projection_metric
        ROI_id = self.structure_tree.get_structures_by_acronym([ROI])[0]["id"] ## UNUSED!!??

        # Loop over all strctures and get projection towards SOI
        results = {"left":[], "right":[], "both":[], "id":[], "acronym":[], "name":[]}

        for origin in self.structures.id.values:
            origin_acronym = self.structures.loc[self.structures.id == origin].acronym.values[0]
            origin_name = self.structures.loc[self.structures.id == origin].name.values[0]

            experiment_data = pd.read_pickle(os.path.join(self.output_data, "{}.pkl".format(origin_acronym)))
            experiment_data = experiment_data.loc[experiment_data.volume > self.volume_threshold]

            exp_target = experiment_data.loc[experiment_data.structure_id == SOI_id] ## BUG! SOI_id is not defined
            exp_target_hemi = self.hemispheres(exp_target.loc[exp_target.hemisphere_id == 1], exp_target.loc[exp_target.hemisphere_id == 2], exp_target.loc[exp_target.hemisphere_id == 3])
            proj_energy = self.hemispheres(np.nanmean(exp_target_hemi.left[projection_metric].values),
                                            np.nanmean(exp_target_hemi.right[projection_metric].values),
                                            np.nanmean(exp_target_hemi.both[projection_metric].values)
            )
            for hemi in self.hemispheres_names:
                results[hemi].append(proj_energy._asdict()[hemi])
            results["id"].append(origin)
            results["acronym"].append(origin_acronym)
            results["name"].append(origin_name)

        results = pd.DataFrame.from_dict(results).sort_values("right", na_position = "first")
        return results

    ####### GET TRACTOGRAPHY AND SPATIAL DATA
    def get_projection_tracts_to_target(self, p0=None, **kwargs):
        """
        Gets tractography data for all experiments whose projections reach the brain region or location of iterest.
        
        :param p0: list of 3 floats with XYZ coordinates of point to be used as seed (Default value = None)
        :param **kwargs: 
        """

        # check args
        if p0 is None:
            raise ValueError("Please pass coordinates")
        elif isinstance(p0, np.ndarray):
            p0 = list(p0)
        elif not isinstance(p0, (list, tuple)):
            raise ValueError("Invalid argument passed (p0): {}".format(p0))

        tract = self.mca.experiment_spatial_search(seed_point=p0, **kwargs)

        if isinstance(tract, str): 
            raise ValueError('Something went wrong with query, query error message:\n{}'.format(tract))
        else:
            return tract


    # ---------------------------------------------------------------------------- #
    #                             STREAMLINES FETCHING                             #
    # ---------------------------------------------------------------------------- #

    def download_streamlines_for_region(self, region, *args, **kwargs):
        """
            Using the Allen Mouse Connectivity data and corresponding API, this function finds expeirments whose injections
            were targeted to the region of interest and downloads the corresponding streamlines data. By default, experiements
            are selected for only WT mice and onl when the region was the primary injection target. Look at "ABA.experiments_source_search"
            to see how to change this behaviour.

            :param region: str with region to use for research
            :param *args: arguments for ABA.experiments_source_search
            :param **kwargs: arguments for ABA.experiments_source_search

        """
        # Get experiments whose injections were targeted to the region
        region_experiments = self.experiments_source_search(region, *args, **kwargs)
        try:
            return self.download_streamlines(region_experiments.id.values)
        except:
            print(f"Could not download streamlines for region {region}")
            return [], [] # <- there were no experiments in the target region 

    def download_streamlines_to_region(self, p0, *args,  mouse_line = "wt", **kwargs):
        """
            Using the Allen Mouse Connectivity data and corresponding API, this function finds injection experiments
            which resulted in fluorescence being found in the target point, then downloads the streamlines data.

            :param p0: list of floats with XYZ coordinates
            :param mouse_line: str with name of the mouse line to use(Default value = "wt")
            :param *args: 
            :param **kwargs: 

        """
        experiments = pd.DataFrame(self.get_projection_tracts_to_target(p0=p0))
        if mouse_line == "wt":
            experiments = experiments.loc[experiments["transgenic-line"] == ""]
        else:
            if not isinstance(mouse_line, list):
                experiments = experiments.loc[experiments["transgenic-line"] == mouse_line]
            else:
                raise NotImplementedError("ops, you've found a bug!. For now you can only pass one mouse line at the time, sorry.")
        return self.download_streamlines(experiments.id.values)


    @staticmethod
    def make_url_given_id(expid):
        """
            Get url of JSON file for an experiment, give it's ID number

            :param expid: int with experiment ID number

        """
        return "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_{}.json.gz".format(expid)

    def extract_ids_from_csv(self, csv_file, download=False, **kwargs):
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
                url = self.make_url_given_id(eid)
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
            return self.download_streamlines(data.id.values, **kwargs)

    def download_streamlines(self, eids, streamlines_folder=None):
        """
            Given a list of expeirmental IDs, it downloads the streamline data from the https://neuroinformatics.nl cache and saves them as
            json files. 

            :param eids: list of integers with experiments IDs
            :param streamlines_folder: str path to the folder where the JSON files should be saved, if None the default is used (Default value = None)

        """
        if streamlines_folder is None:
            streamlines_folder = self.streamlines_cache

        if not isinstance(eids, (list, np.ndarray, tuple)): eids = [eids]

        filepaths, data = [], []
        for eid in tqdm(eids):
            url = self.make_url_given_id(eid)
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
