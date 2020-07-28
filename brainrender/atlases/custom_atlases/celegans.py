import pandas as pd

# import numpy as np
import os
from PIL import ImageColor
import math

from vedo import load, merge, write, Points, Arrows
from vedo.shapes import Tube
from vedo.analysis import recoSurface

from brainrender.scene import Scene
from brainrender.Utils.paths_manager import Paths
from brainrender.Utils.data_io import (
    load_mesh_from_file,
    listdir,
    get_subdirs,
    load_json,
)
from brainrender.colors import get_random_colors  # , getColor
from brainrender import NEURON_RESOLUTION, ROOT_ALPHA, ROOT_COLOR

# TODO add method to select pre/post synapses based on synaptic partner


"""
This class rendereds datasets of the whole C. Elegans connectome. 
All data from Daniel Witvliet and co-authors.
Check https://www.biorxiv.org/content/10.1101/2020.04.30.066209v1 
for more details.


Note: currently there is no support to let users download the
connectome data programmatically. If you need the data please
get in touch. We are working to improve this.


check example file at Examples/custom_atlases/celegans_connectome.py
for more details

"""


class Celegans(Paths):
    atlas_name = "Celegans"
    mesh_format = "obj"  #  or obj, stl etc..

    pre_synapses_color = "darkgray"
    post_synapses_color = "blackboard"
    synapses_radius = 0.2

    skeleton_radius = 0.05

    default_camera = dict(
        position=[-15.686, 65.978, 32.901],
        focal=[13.312, 20.159, -9.482],
        viewup=[-0.896, -0.412, -0.168],
        distance=68.823,
        clipping=[26.154, 122.7],
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
        Paths.__init__(self, base_dir, **kwargs)

        # Get data
        if data_folder is None:
            raise ValueError(
                "No data folder was passed, use the 'atlas_kwargs' argument of Scene to pass a data folder path"
            )
        if not os.path.isdir(data_folder):
            raise FileNotFoundError(f"The folder {data_folder} does not exist")
        self.data_folder = data_folder
        self._get_data()

    def _make_root(self, rootpath):
        """
            Creates a root mesh by merging the mesh corresponding to each neuron,
            then saves it as an obj file at rootpath
        """
        raise NotImplementedError(
            "Create root method not supported yet, sorry"
        )

        print(f"Creating root mesh for atlas {self.atlas_name}")
        temp_scene = Scene(
            atlas=Celegans,
            add_root=False,
            display_inset=False,
            atlas_kwargs=dict(data_folder=self.data_folder),
        )

        temp_scene.add_neurons(self.neurons_names)
        temp_scene.render(interactive=False)
        temp_scene.close()

        root = merge(*temp_scene.actors["neurons"]).clean().cap()
        # root = mesh2Volume(root, spacing=(0.02, 0.02, 0.02)).isosurface()

        points = Points(root.points()).smoothMLS2D(f=0.8).clean(tol=0.005)

        root = recoSurface(points, dims=100, radius=0.2)

        # Save
        write(root, rootpath)

        del temp_scene
        return root

    # ----------------------------------- Utils ---------------------------------- #
    def get_neurons_by(self, getby="pair", lookup=None):
        """
            Selects a subset of the neurons using some criteria and lookup key, 
            based on the neurons metadata

            :param getby: str, name of the metadata key to use for selecting neurons
            :param lookup: str/int.. neurons whose attribute 'getby' matches the lookup value will be selected

            :returns: list of strings with neurons names
        """
        try:  # make this work if called by a Scene class
            cs = self.atlas
        except:
            cs = self

        allowed = ["neuron", "pair", "class", "type"]

        if getby not in allowed:
            raise ValueError(
                f"Get by key should be one of {allowed} not {getby}"
            )

        filtered = list(
            cs.neurons_metadata.loc[cs.neurons_metadata[getby] == lookup][
                "neuron"
            ].values
        )
        if not filtered:
            print(f"Found 0 neurons with getby {getby} and lookup {lookup}")

        return filtered

    def get_neuron_color(self, neuron, colorby="type"):
        """
            Get a neuron's RGB color. Colors can be assigned based on different criteria
            like the neuron's type or by individual neuron etc...

            :param neuron: str, nueron name
            :param colorby: str, metadata attribute to use for coloring
            :returns: rgb values of color
        """
        try:  # make this work if called by a Scene class
            cs = self.atlas
        except:
            cs = self

        allowed = ["neuron", "individual", "ind", "pair", "class", "type"]

        if colorby not in allowed:
            raise ValueError(
                f"color by key should be one of {allowed} not {colorby}"
            )

        if colorby == "type":
            color = cs.neurons_metadata.loc[
                cs.neurons_metadata.neuron == neuron
            ]["type_color"].values[0]
            color = ImageColor.getrgb(color)
        elif (
            colorby == "individual" or colorby == "ind" or colorby == "neuron"
        ):
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
            raise ValueError(
                "The data folder should include a subfolder which stores the neurons .obj files"
            )

        try:
            self.objs_fld = [f for f in subdirs if "objs_smoothed" in f][0]
        except:
            raise FileNotFoundError(
                "Could not find subdirectory with .obj files"
            )

        # Get filepath to each .obj
        self.neurons_files = [
            f for f in listdir(self.objs_fld) if f.lower().endswith(".obj")
        ]

        # Get synapses and skeleton files
        try:
            skeletons_file = [
                f
                for f in listdir(self.data_folder)
                if f.endswith("skeletons.json")
            ][0]
        except:
            raise FileNotFoundError(
                "Could not find file with neurons skeleton data"
            )

        try:
            synapses_file = [
                f
                for f in listdir(self.data_folder)
                if f.endswith("synapses.csv")
            ][0]
        except:
            raise FileNotFoundError("Could not find file with synapses data")

        # load data
        self.skeletons_data = load_json(skeletons_file)
        self.synapses_data = pd.read_csv(synapses_file, sep=";")

        # Get neurons metadata
        try:
            metadata_file = [
                f
                for f in listdir(self.data_folder)
                if "neuron_metadata.csv" in f
            ][0]
        except:
            raise FileNotFoundError(
                f"Could not find neurons metadata file {metadata_file}"
            )

        self.neurons_metadata = pd.read_csv(metadata_file)
        self.neurons_names = list(self.neurons_metadata.neuron.values)

    def _check_neuron_argument(self, neurons):
        """
            Checks if a list of string includes neurons name, returns only
            elements of the list that are correct names

            :param neurons: list of strings with neurons names
        """
        try:  # make this work if called by a Scene class
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
        try:  # make this work if called by a Scene class
            cs = self.atlas
        except:
            cs = self
        try:
            data = cs.skeletons_data[neuron]
        except:
            print(f"No skeleton data found for {neuron}")
            return None

        # Create an actor for each neuron's branch and then merge
        actors = []
        for branch in data["branches"]:
            coords = [data["coordinates"][str(p)] for p in branch]

            # Just like for synapses we need to adjust the coordinates to match the .obj files
            # coords are x z -y
            adjusted_coords = [(c[0], c[2], -c[1]) for c in coords]
            actors.append(
                Tube(
                    adjusted_coords,
                    r=cs.skeleton_radius,
                    res=NEURON_RESOLUTION,
                )
            )

        return merge(*actors)

    # ------------------------------- Atlas methods ------------------------------ #
    def _get_structure_mesh(self, acronym, **kwargs):
        """
            Get's the mesh for a brainregion, for this atlas it's just for
            getting/making the root mesh

        """
        if acronym != "root":
            raise ValueError(
                f"The atlas {self.atlas_name} only has one structure mesh: root. Argument {acronym} is not valid"
            )

        objpath = os.path.join(self.data_folder, "objs_smoothed", "root2.obj")
        if not os.path.isfile(objpath):
            root = self._make_root(objpath)
        else:
            root = load(objpath)

        root.c(ROOT_COLOR).alpha(ROOT_ALPHA)

        return root

    def get_neurons(self, neurons, alpha=1, as_skeleton=False, colorby="type"):
        """
            Renders neurons and adds returns to the scene. 

            :param neurons: list of names of neurons
            :param alpha: float in range 0,1 -  neurons transparency
            :param as_skeleton: bool (Default value = False), if True neurons are rendered as skeletons 
                                otherwise as a full mesh showing the whole morphology
            :param colorby: str, criteria to use to color the neurons. Accepts values like type, individual etc. 
        """
        neurons = self._check_neuron_argument(neurons)

        actors, store = [], {}
        for neuron in neurons:
            if neuron not in self.neurons_names:
                print(f"Neuron {neuron} not included in dataset")
            else:
                color = self.get_neuron_color(neuron, colorby=colorby)

                if as_skeleton:  # reconstruct skeleton from json
                    actor = self._parse_neuron_skeleton(neuron)

                else:  # load as .obj file
                    try:
                        neuron_file = [
                            f for f in self.neurons_files if neuron in f
                        ][0]
                    except:
                        print(f"Could not find .obj file for neuron {neuron}")
                        continue

                    actor = load_mesh_from_file(neuron_file)

                if actor is not None:
                    # Refine actor's look
                    actor.alpha(alpha).c(color)

            actors.append(actor)
            store[neuron] = (actor, as_skeleton)

        return actors, store

    def get_neurons_synapses(
        self,
        scene_store,
        neurons,
        alpha=1,
        pre=False,
        post=False,
        colorby="synapse_type",
        draw_patches=False,
        draw_arrows=True,
    ):
        """
            THIS METHODS GETS CALLED BY SCENE, self referes to the instance of Scene not to this class.
            Renders neurons and adds them to the scene. 

            :param neurons: list of names of neurons
            :param alpha: float in range 0,1 -  neurons transparency
            :param pre: bool, if True the presynaptic sites of each neuron are rendered
            :param post: bool, if True the postsynaptic sites on each neuron are rendered
            :param colorby: str, criteria to use to color the neurons.
                             Accepts values like synapse_type, type, individual etc. 
            :param draw_patches: bool, default True. If true dark patches are used to show the location of post synapses
            :param draw_arrows: bool, default True. If true arrows are used to show the location of post synapses
        """

        col_names = ["x", "z", "y"]
        # used to correctly position synapses on .obj files

        neurons = self._check_neuron_argument(neurons)

        spheres_data, actors = [], []
        for neuron in neurons:
            if pre:
                if colorby == "synapse_type":
                    color = self.pre_synapses_color
                else:
                    color = self.get_neuron_color(neuron, colorby=colorby)

                data = self.synapses_data.loc[self.synapses_data.pre == neuron]
                if not len(data):
                    print(f"No pre- synapses found for neuron {neuron}")
                else:
                    data = data[["x", "y", "z"]]
                    data["y"] = -data["y"]

                    spheres_data.append(
                        (
                            data,
                            dict(
                                color=color,
                                verbose=False,
                                alpha=alpha,
                                radius=self.synapses_radius,
                                res=24,
                                col_names=col_names,
                            ),
                        )
                    )

            if post:
                if colorby == "synapse_type":
                    color = self.post_synapses_color
                else:
                    color = self.get_neuron_color(neuron, colorby=colorby)

                rows = [
                    i
                    for i, row in self.synapses_data.iterrows()
                    if neuron in row.posts
                ]
                data = self.synapses_data.iloc[rows]

                if not len(data):
                    print(f"No post- synapses found for neuron {neuron}")
                else:
                    data = data[["x", "y", "z"]]
                    data["y"] = -data["y"]

                    """
                        Post synaptic locations are shown as darkening of patches
                        of a neuron's mesh and or as a 3d arrow point toward the neuron.
                    """

                    spheres_data.append(
                        (
                            data,
                            dict(
                                color="black",
                                verbose=False,
                                alpha=0,
                                radius=self.synapses_radius * 4,
                                res=24,
                                col_names=col_names,
                            ),
                        )
                    )

                    # Get mesh points for neuron the synapses belong to
                    if neuron not in scene_store.keys():
                        neuron_file = [
                            f for f in self.neurons_files if neuron in f
                        ][0]
                        neuron_act = load_mesh_from_file(neuron_file, c=color)
                    else:
                        neuron_act, as_skeleton = scene_store[neuron]

                    # Draw post synapses as dark patches
                    if draw_patches:
                        if as_skeleton:
                            print(
                                "Can't display post synapses as dark spots when neron is rendered in skeleton mode"
                            )
                        else:
                            # Get faces that are inside the synapses spheres and color them darker
                            raise NotImplementedError("This needs some fixing")

                            # neuron_points = neuron_act.cellCenters()
                            # inside_points = spheres.insidePoints(
                            #     neuron_points, returnIds=True
                            # )

                            # n_cells = neuron_act.polydata().GetNumberOfCells()
                            # scals = np.zeros((n_cells))
                            # scals[inside_points] = 1

                            # colors = [
                            #     neuron_act.c()
                            #     if s == 0
                            #     else getColor("blackboard")
                            #     for s in scals
                            # ]
                            # neuron_act.cellIndividualColors(colors)

                    # Draw post synapses as arrow
                    if draw_arrows:
                        points1 = [
                            [x, y, z]
                            for x, y, z in zip(
                                data[col_names[0]].values,
                                data[col_names[1]].values,
                                data[col_names[2]].values,
                            )
                        ]

                        points2 = [neuron_act.closestPoint(p) for p in points1]

                        #  shift point1 to make arrows longer
                        def dist(p1, p2):
                            return math.sqrt(
                                (p1[0] - p2[0]) ** 2
                                + (p1[1] - p2[1]) ** 2
                                + (p1[2] - p2[2]) ** 2
                            )

                        def get_point(p1, p2, d, u):
                            alpha = (1 / d) * u
                            x = (1 - alpha) * p1[0] + alpha * p2[0]
                            y = (1 - alpha) * p1[1] + alpha * p2[1]
                            z = (1 - alpha) * p1[2] + alpha * p2[2]
                            return [x, y, z]

                        dists = [
                            dist(p1, p2) for p1, p2 in zip(points1, points2)
                        ]
                        points0 = [
                            get_point(p1, p2, d, -0.5)
                            for p1, p2, d in zip(points1, points2, dists)
                        ]

                        arrows = Arrows(
                            points0, endPoints=points2, c=color, s=4
                        )

                        # ! aasduaisdbasiudbuia
                        actors.append(arrows)
        return spheres_data, actors
