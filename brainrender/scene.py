import brainrender

import numpy as np
import os
import datetime
import random
from vedo import (
    Plotter,
    shapes,
    show,
    screenshot,
    interactive,
    Text2D,
    closePlotter,
    settings,
    Plane,
    Text,
    Sphere,
)
from vedo.shapes import Cylinder, Line
from vedo.mesh import Mesh as Actor
import pandas as pd
from pathlib import Path
import brainatlas_api

from brainrender.colors import getColor, get_random_colors
from brainrender.atlases.mouse import ABA25Um
from brainrender.Utils.data_io import (
    load_mesh_from_file,
    get_probe_points_from_sharptrack,
)
from brainrender.atlases import generate_bgatlas_on_the_fly
from brainrender.Utils.data_manipulation import flatten_list, return_list_smart
from brainrender.Utils import actors_funcs
from brainrender.Utils.camera import check_camera_param, set_camera


class Scene:  # subclass brain render to have acces to structure trees
    """
        The code below aims to create a scene to which actors can be added or removed, changed etc..
        It also facilitates the interaction with the scene (e.g. moving the camera) and the creation of
        snapshots or animated videos.
        The class Scene is based on the Plotter class of vedo: https://github.com/marcomusy/vedo/blob/master/vedo/plotter.py
        and other classes within the same package.
    """

    verbose = brainrender.VERBOSE

    def __init__(
        self,
        brain_regions=None,
        regions_aba_color=False,
        neurons=None,
        tracts=None,
        add_root=None,
        verbose=True,
        jupyter=False,
        display_inset=None,
        base_dir=None,
        camera=None,
        screenshot_kwargs={},
        use_default_key_bindings=False,
        title=None,
        atlas=None,
        atlas_kwargs=dict(),
        **kwargs,
    ):
        """

            Creates and manages a Plotter instance

            :param brain_regions: list of brain regions acronyms to be added to the rendered scene (default value None)
            :param regions_aba_color: if True, use the Allen Brain Atlas regions colors (default value None)
            :param neurons: path to JSON or SWC file with data of neurons to be rendered [or list of files] (default value None)
            :param tracts: list of JSON files with tractography data to be rendered (default value None)
            :param add_root: if False a rendered outline of the whole brain is added to the scene (default value None)
            :param verbose: if False less feedback is printed to screen (default value True)
            :param display_insert: if False the inset displaying the brain's outline is not rendered (but the root is added to the scene) (default value None)
            :param base_dir: path to directory to use for saving data (default value None)
            :param camera: name of the camera parameters setting to use (controls the orientation of the rendered scene)
            :param kwargs: can be used to pass path to individual data folders. See brainrender/Utils/paths_manager.py
            :param screenshot_kwargs: pass a dictionary with keys:
                        - 'folder' -> str, path to folder where to save screenshots
                        - 'name' -> str, filename to prepend to screenshots files
                        - 'format' -> str, 'png', 'svg' or 'jpg'
                        - scale -> float, values > 1 yield higher resultion screenshots
            :param use_default_key_bindings: if True the defualt keybindings from vedo are used, otherwise
                            a custom function that can be used to take screenshots with the parameter above. 
            :param title: str, if a string is passed a text is added to the top of the rendering window as a title
            :param atlas: an instance of a valid Atlas class to use to fetch anatomical data for the scene. By default
                if not atlas is passed the allen brain atlas for the adult mouse brain is used. If a string with the atlas
                name is passed it will try to load the corresponding brainglobe atlas.
            :param atlas_kwargs: dictionary used to pass extra arguments to atlas class
        """
        if atlas is None:
            self.atlas = ABA25Um(base_dir=base_dir, **atlas_kwargs, **kwargs)
        else:
            if not isinstance(atlas, str):
                self.atlas = atlas(base_dir=base_dir, **atlas_kwargs, **kwargs)
            else:
                atlas_class = brainatlas_api.get_atlas_class_from_name(atlas)
                if atlas_class is None:
                    raise ValueError(
                        f"Atlas name passed [{atlas}] is not a recognised atlas"
                    )
                else:
                    self.atlas = generate_bgatlas_on_the_fly(
                        atlas_class, atlas
                    )

        # Setup a few rendering options
        self.verbose = verbose
        self.regions_aba_color = regions_aba_color

        # Infer if we are using k3d from vedo.settings
        if settings.notebookBackend == "k3d":
            self.jupyter = True
        else:
            self.jupyter = False

        if display_inset is None:
            self.display_inset = brainrender.DISPLAY_INSET
        else:
            self.display_inset = display_inset

        if self.display_inset and jupyter:
            print(
                "Setting 'display_inset' to False as this feature is not available in juputer notebooks"
            )
            self.display_inset = False

        if add_root is None:
            add_root = brainrender.DISPLAY_ROOT

        # Camera parameters
        if camera is None:
            if self.atlas.default_camera is not None:
                self.camera = check_camera_param(self.atlas.default_camera)
            else:
                self.camera = brainrender.CAMERA
        else:
            self.camera = check_camera_param(camera)

        # Set up vedo plotter and actors records
        if brainrender.WHOLE_SCREEN and not self.jupyter:
            sz = "full"
        elif brainrender.WHOLE_SCREEN and self.jupyter:
            print(
                "Setting window size to 'auto' as whole screen is not available in jupyter"
            )
            sz = "auto"
        else:
            sz = "auto"

        if brainrender.SHOW_AXES:
            axes = 1
        else:
            axes = 0

        # Create plotter
        self.plotter = Plotter(
            axes=axes, size=sz, pos=brainrender.WINDOW_POS, title="brainrender"
        )
        self.plotter.legendBC = getColor("blackboard")

        # SCreenshots and keypresses variables
        self.screenshots_folder = screenshot_kwargs.pop(
            "folder", self.atlas.output_screenshots
        )
        self.screenshots_name = screenshot_kwargs.pop(
            "name", brainrender.DEFAULT_SCREENSHOT_NAME
        )
        self.screenshots_extension = screenshot_kwargs.pop(
            "type", brainrender.DEFAULT_SCREENSHOT_TYPE
        )
        self.screenshots_scale = screenshot_kwargs.pop(
            "scale", brainrender.DEFAULT_SCREENSHOT_SCALE
        )

        if not use_default_key_bindings:
            self.plotter.keyPressFunction = self.keypress
            self.verbose = False

        if not brainrender.SCREENSHOT_TRANSPARENT_BACKGROUND:
            settings.screenshotTransparentBackground = False
            settings.useFXAA = True

        # Prepare store for actors added to scene
        self.actors = {
            "regions": {},
            "tracts": [],
            "neurons": [],
            "root": None,
            "others": [],
            "labels": [],
        }
        self._actors = None  # store a copy of the actors when manipulations like slicing are done
        self.store = {}  # in case we need to store some data

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

        if title is not None:
            self.add_text(title)

        # Placeholder variables
        self.inset = None  # the first time the scene is rendered create and store the inset here
        self.is_rendered = (
            False  # keep track of if the scene has already been rendered
        )

    # ---------------------------------------------------------------------------- #
    #                                     Utils                                    #
    # ---------------------------------------------------------------------------- #
    def _check_point_in_region(self, point, region_actor):
        """
            Checks if a point of defined coordinates is within the mesh of a given actorr

            :param point: 3-tuple or list of xyz coordinates
            :param region_actor: vedo actor
        """
        if not region_actor.insidePoints([point]):
            return False
        else:
            return True

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
                if self.root is None:
                    print("Could not find root object")
                    return

                self.inset = self.root.clone().scale(0.5)
                self.root = None
                self.actors["root"] = None
            else:
                self.inset = self.root.clone().scale(0.5)

            self.inset.alpha(1)
            self.plotter.showInset(
                self.inset, pos=(0.95, 0.1), draggable=False
            )

    def get_n_random_points_in_region(self, region, N, hemisphere=None):
        """
        Gets N random points inside (or on the surface) of the mesh defining a brain region.

        :param region: str, acronym of the brain region.
        :param N: int, number of points to return.
        """
        if isinstance(region, Actor):
            region_mesh = region
        else:
            if hemisphere is None:
                region_mesh = self.atlas._get_structure_mesh(region)
            else:
                region_mesh = self.atlas.get_region_unilateral(
                    region, hemisphere=hemisphere
                )
            if region_mesh is None:
                return None

        region_bounds = region_mesh.bounds()

        X = np.random.randint(region_bounds[0], region_bounds[1], size=10000)
        Y = np.random.randint(region_bounds[2], region_bounds[3], size=10000)
        Z = np.random.randint(region_bounds[4], region_bounds[5], size=10000)
        pts = [[x, y, z] for x, y, z in zip(X, Y, Z)]

        try:
            ipts = region_mesh.insidePoints(pts).points()
        except:
            ipts = region_mesh.insidePoints(
                pts
            )  # to deal with older instances of vedo
        return random.choices(ipts, k=N)

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

    def mirror_actor_hemisphere(self, actors):
        """
            Mirrors actors from one hemisphere to the next
        """
        if not isinstance(actors, list):
            actors = [actors]

        for actor in actors:
            mirror_coord = self.atlas.get_region_CenterOfMass(
                "root", unilateral=False
            )[2]
            actors_funcs.mirror_actor_at_point(actor, mirror_coord, axis="x")

    def cut_actors_with_plane(
        self,
        plane,
        actors=None,
        showplane=False,
        returncut=False,
        close_actors=False,
        **kwargs,
    ):
        # Check arguments
        if isinstance(plane, (list, tuple)):
            planes = plane.copy()
        else:
            planes = [plane]

        if actors is None:
            actors = self.get_actors()
        else:
            if not isinstance(actors, (list, tuple)):
                actors = [actors]

        # Loop over each plane
        to_return = []
        for plane in planes:
            # Get the plane actor
            if isinstance(plane, str):
                if plane == "sagittal":
                    plane = self.atlas.get_sagittal_plane(**kwargs)
                elif plane == "coronal":
                    plane = self.atlas.get_coronal_plane(**kwargs)
                elif plane == "horizontal":
                    plane = self.atlas.get_horizontal_plane(**kwargs)
                else:
                    raise ValueError(f"Unrecognized plane name: {plane}")
            else:
                if not isinstance(plane, Plane):
                    raise ValueError(
                        "The plane arguments should either be a Plane actor or"
                        + "a string with the name of predefined planes."
                        + f" Not: {plane.__type__}"
                    )

            # Show plane
            if showplane:
                self.add_actor(plane)

            # Cut actors
            for actor in actors:
                if actor is None:
                    continue
                actor = actor.cutWithPlane(
                    origin=plane.center,
                    normal=plane.normal,
                    returnCut=returncut,
                )
                if returncut:
                    to_return.append(actor)

                if close_actors:
                    actor.cap()

        if len(to_return) == 1:
            return to_return[0]
        else:
            return to_return

    # ------------------------------ Cells functions ----------------------------- #
    def get_cells_in_region(self, cells, region):
        """
            Selects the cells that are in a list of user provided regions from a dataframe of cell locations

            :param cells: pd.DataFrame of cells x,y,z coordinates
        """
        if isinstance(region, list):
            region_list = []
            for reg in region:
                region_list.extend(
                    list(self.get_structure_descendants(reg)["acronym"].values)
                )
        else:
            region_list = list(
                self.atlas.get_structure_descendants(region)["acronym"].values
            )
        return cells[cells.region.isin(region_list)]

    # ---------------------------------------------------------------------------- #
    #                                POPULATE SCENE                                #
    # ---------------------------------------------------------------------------- #

    # ------------------------------- Atlas methods ------------------------------ #
    # Each Atlas class overwrites some of these methods with atlas-specific methods.
    # Different atlses will overwrite different sets of methods, therefore supporting
    # different functionality.

    def add_root(self, render=True, **kwargs):
        """
        adds the root the scene (i.e. the whole brain outline)

        :param render:  (Default value = True)
        :param **kwargs:

        """
        if not render:
            self.root = self.atlas._get_structure_mesh(
                "root", c=brainrender.ROOT_COLOR, alpha=0, **kwargs
            )
        else:
            self.root = self.atlas._get_structure_mesh(
                "root",
                c=brainrender.ROOT_COLOR,
                alpha=brainrender.ROOT_ALPHA,
                **kwargs,
            )

        if self.root is None:
            print("Could not find a root mesh")
            return None

        # # get the center of the root and the bounding box + update for atlas
        # self.atlas._root_midpoint = self.root.centerOfMass()
        # self.atlas._root_bounds = [self.root.xbounds(), self.root.ybounds(), self.root.zbounds()]

        if render:
            self.actors["root"] = self.root

        return self.root

    def add_brain_regions(self, *args, **kwargs):
        """
            Adds brain regions meshes to scene.
            Check the atlas' method to know how it works
        """
        add_labels = kwargs.pop("add_labels", False)

        allactors = self.atlas.get_brain_regions(
            *args, verbose=self.verbose, **kwargs
        )

        actors = []
        for region, actor in allactors.items():
            if region in self.actors["regions"].keys():
                # Avoid inserting again
                continue

            if add_labels:
                self.add_actor_label(actor, region, **kwargs)

            self.actors["regions"][region] = actor
            actors.append(actor)

        return return_list_smart(actors)

    def add_neurons(self, *args, **kwargs):
        """
        Adds rendered morphological data of neurons reconstructions.
        Check the atlas' method to know how it works
        """
        actors, store = self.atlas.get_neurons(*args, **kwargs)
        if isinstance(actors, list):
            self.actors["neurons"].extend(actors)
        else:
            self.actors["neurons"].append(actors)
            actors = [actors]

        if store is not None:
            for n, v in store.items():
                self.store[n] = v

        return return_list_smart(actors)

    def add_neurons_synapses(self, *args, **kwargs):
        """
        Adds the location of pre or post synapses for a neuron (or list of neurons).
        Check the atlas' method to know how it works. 
        """
        spheres_data, actors = self.atlas.get_neurons_synapses(
            self.store, *args, **kwargs
        )

        for data, kwargs in spheres_data:
            self.add_cells(data, **kwargs)

        for actor in actors:
            self.add_actor(actor)

    def add_tractography(self, *args, **kwargs):
        """
        Renders tractography data and adds it to the scene. 
        Check the function definition in ABA for more details
        """

        actors = self.atlas.get_tractography(*args, **kwargs)
        self.actors["tracts"].extend(actors)
        return return_list_smart(actors)

    def add_streamlines(self, *args, **kwargs):
        """
        Render streamline data.
        Check the function definition in ABA for more details
        """
        actors = self.atlas.get_streamlines(*args, **kwargs)
        self.actors["tracts"].extend(actors)
        return return_list_smart(actors)

    # -------------------------- General actors/elements ------------------------- #
    def add_actor(self, *actors, store=None):
        """
        Add a vtk actor to the scene

        :param actor:
        :param store: one of the items in self.actors to use to store the actor
                being created. It needs to be a list

        """
        # TODO add a check that the arguments passed are indeed vtk actors?

        to_return = []
        for actor in actors:
            if store is None:
                self.actors["others"].append(actor)
            else:
                if not isinstance(store, list):
                    raise ValueError("Store should be a list")
                store.append(actor)

            to_return.append(actor)

        return return_list_smart(to_return)

    def add_mesh_silhouette(self, *actors, lw=1, color="k", **kwargs):
        """
            Given a list of actors it adds a colored silhouette
            to them.
        """
        for actor in actors:
            self.add_actor(actor.silhouette(**kwargs).lw(lw).c(color))

    def add_from_file(self, *filepaths, **kwargs):
        """
        Add data to the scene by loading them from a file. Should handle .obj, .vtk and .nii files.

        :param filepaths: path to the file. Can pass as many arguments as needed
        :param **kwargs:

        """
        actors = []
        for filepath in filepaths:
            actor = load_mesh_from_file(filepath, **kwargs)
            self.actors["others"].append(actor)
            actors.append(actor)

        return return_list_smart(actors)

    def add_sphere_at_point(
        self, pos=[0, 0, 0], radius=100, color="black", alpha=1, **kwargs
    ):
        """
        Adds a shere at a location specified by the user

        :param pos: list of x,y,z coordinates (Default value = [0, 0, 0])
        :param radius: int, radius of the sphere (Default value = 100)
        :param color: color of the sphere (Default value = "black")
        :param alpha: transparency of the sphere (Default value = 1)
        :param **kwargs:
        """
        sphere = shapes.Sphere(
            pos=pos, r=radius, c=color, alpha=alpha, **kwargs
        )
        self.actors["others"].append(sphere)
        return sphere

    def add_cells_from_file(
        self, filepath, hdf_key="hdf", color="red", radius=25, res=3, alpha=1
    ):
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
        supported_formats = brainrender.HDF_SUFFIXES + [csv_suffix]

        #  check that the filepath makes sense
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(filepath)

        # check that the file is of the supported types
        if filepath.suffix == csv_suffix:
            cells = pd.read_csv(filepath)
            self.add_cells(
                cells, color=color, radius=radius, res=res, alpha=alpha
            )

        elif filepath.suffix in supported_formats:
            # parse file and load cell locations
            if filepath.suffix in brainrender.HDF_SUFFIXES:
                if hdf_key is None:
                    hdf_key = brainrender.DEFAULT_HDF_KEY
                try:
                    cells = pd.read_hdf(filepath, key=hdf_key)
                except TypeError:
                    if hdf_key == brainrender.DEFAULT_HDF_KEY:
                        raise ValueError(
                            f"The default identifier: {brainrender.DEFAULT_HDF_KEY} "
                            f"cannot be found in the hdf file. Please supply "
                            f"a key using 'scene.add_cells_from_file(filepath, "
                            f"hdf_key='key'"
                        )
                    else:
                        raise ValueError(
                            f"The key: {hdf_key} cannot be found in the hdf "
                            f"file. Please check the correct identifer."
                        )
            return self.add_cells(
                cells, color=color, radius=radius, res=res, alpha=alpha
            )

        elif filepath.suffix == ".pkl":
            cells = pd.read_pikle(filepath)
            return self.add_cells(
                cells, color=color, radius=radius, res=res, alpha=alpha
            )
        else:
            raise NotImplementedError(
                f"File format: {filepath.suffix} is not currently supported. "
                f"Please use one of: {supported_formats}"
            )

    def add_cells(
        self,
        coords,
        color="red",
        color_by_region=False,
        color_by_metadata=None,
        radius=25,
        res=3,
        alpha=1,
        col_names=None,
        regions=None,
        verbose=True,
    ):
        """
        Renders cells given their coordinates as a collection of spheres.

        :param coords: pandas dataframe with x,y,z coordinates
        :param color: str, color of spheres used to render the cells (Default value = "red"). 
                Alternatively a list of colors specifying the color of each cell.
        :param radius: int, radius of spheres used to render the cells (Default value = 25)
        :param res: int, resolution of spheres used to render the cells (Default value = 3)
        :param alpha: float, transparency of spheres used to render the cells (Default value = 1)
        :param color_by_region: bool. If true the cells are colored according to the color of the brain region they are in
        :param color_by_metadata: str, if the name of a column of the coords dataframe is passed, cells are colored according 
                to their value for that column. If color_by_metadata is passed and a dictionary is passed
                to 'color' at the same time, the dictionary will be used to specify the colors used. Therefore
                `color` should map values in the metadata column to colors
        :param regions: if a list of brain regions acronym is passed, only cells in these regions will be added to the scene
        :param col_names: list of strings with names of pandas dataframe columns. If passed it should be a list of 3 columns
                which have the x, y, z coordinates. If not passed, it is assumed that the columns are ['x', 'y', 'z']
        """
        if isinstance(coords, pd.DataFrame):
            coords_df = coords.copy()  # keep a copy
            if col_names is None:
                col_names = ["x", "y", "z"]
            else:
                if not isinstance(col_names, (list, tuple)):
                    raise ValueError(
                        "Column names should be a list of 3 columns"
                    )
                if not len(col_names) == 3:
                    raise ValueError(
                        "Column names should be a list of 3 columns"
                    )

            if regions is not None:
                coords = self.get_cells_in_region(coords, regions)
            coords = [
                [x, y, z]
                for x, y, z in zip(
                    coords[col_names[0]].values,
                    coords[col_names[1]].values,
                    coords[col_names[2]].values,
                )
            ]
        else:
            raise ValueError("Unrecognized argument for cell coordinates")

        if color_by_region:
            color = self.atlas.get_colors_from_coordinates(coords)

        elif color_by_metadata is not None:
            if color_by_metadata not in coords_df.columns:
                raise ValueError(
                    'Color_by_metadata argument should be the name of one of the columns of "coords"'
                )

            # Get a map from metadata values to colors
            vals = list(coords_df[color_by_metadata].values)
            if len(vals) == 0:
                raise ValueError(
                    f"Cant color by {color_by_metadata} as no values were found"
                )
            if not isinstance(
                color, dict
            ):  # The user didn't pass a lookup, generate random
                base_cols = get_random_colors(n_colors=len(set(vals)))
                cols_lookup = {v: c for v, c in zip(set(vals), base_cols)}
            else:
                try:
                    for val in list(set(vals)):
                        color[val]
                except KeyError:
                    raise ValueError(
                        'While using "color_by_metadata" with a dictionary of colors passed'
                        + ' to "color", not every metadata value was assigned a color in the dictionary'
                        + " please make sure that the color dictionary is complete"
                    )
                else:
                    cols_lookup = color

            # Use the map to get a color for each cell
            color = [cols_lookup[v] for v in vals]

        spheres = shapes.Spheres(
            coords, c=color, r=radius, res=res, alpha=alpha
        )
        self.actors["others"].append(spheres)

        if verbose:
            print("Added {} cells to the scene".format(len(coords)))

        return spheres

    def add_optic_cannula(
        self,
        target_region=None,
        pos=None,
        x_offset=0,
        y_offset=0,
        z_offset=-500,
        use_line=False,
        **kwargs,
    ):
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
        hemisphere = kwargs.pop("hemisphere", "right")
        color = kwargs.pop("color", "powderblue")
        radius = kwargs.pop("radius", 350)
        alpha = kwargs.pop("alpha", 0.5)

        # Get coordinates of brain-side face of optic cannula
        if target_region is not None:
            pos = self.atlas.get_region_CenterOfMass(
                target_region, unilateral=True, hemisphere=hemisphere
            )
        elif pos is None:
            print(
                "No 'pos' or 'target_region' arguments were \
                            passed to 'add_optic_cannula', nothing to render"
            )
            return
        else:
            if not len(pos) == 3:
                raise ValueError(
                    f"Invalid target coordinates argument, pos: {pos}"
                )

        # Offset position
        pos[0] += y_offset
        pos[1] += z_offset
        pos[2] += x_offset

        # Get coordinates of upper face
        bounds = self.root.bounds()
        top = pos.copy()
        top[1] = bounds[2] - 500

        if not use_line:
            cylinder = self.add_actor(
                Cylinder(
                    pos=[top, pos], c=color, r=radius, alpha=alpha, **kwargs
                )
            )
        else:
            cylinder = self.add_actor(
                Line(top, pos, c=color, alpha=alpha, lw=radius)
            )
        return cylinder

    def add_text(self, text, **kwargs):
        """
            Adds a 2D text to the scene. Default params are to crate a large black
            text at the top of the rendering window.

            :param text: str with text to write
            :param kwargs: keyword arguments accepted by vedo.shapes.Text2D
        """
        pos = kwargs.pop("pos", 8)
        size = kwargs.pop("size", 1.75)
        color = kwargs.pop("color", "k")
        alpha = kwargs.pop("alpha", 1)
        font = kwargs.pop("font", "Montserrat")

        txt = self.add_actor(
            Text2D(text, pos=pos, s=size, c=color, alpha=alpha, font=font)
        )
        return txt

    def add_actor_label(self, actors, labels, **kwargs):
        """
            Adds a 2D text ancored to a point on the actor's mesh
            to label what the actor is

            :param kwargs: key word arguments can be passed to determine 
                    text appearance and location:
                        - size: int, text size. Default 300
                        - color: str, text color. A list of colors can be passed
                                if None the actor's color is used. Default None.
                        - xoffset, yoffset, zoffset: integers that shift the label position
                        - radius: radius of sphere used to denote label anchor. Set to 0 or None to hide. 
        """
        # Check args
        if not isinstance(actors, (tuple, list)):
            actors = [actors]
        if not isinstance(labels, (tuple, list)):
            labels = [labels]

        # Get text params
        size = kwargs.pop("size", 300)
        color = kwargs.pop("color", None)
        radius = kwargs.pop("radius", 100)

        xoffset = kwargs.pop("xoffset", 0)
        yoffset = kwargs.pop("yoffset", 0)
        zoffset = kwargs.pop("zoffset", 0)

        if self.atlas.atlas_name == "ABA":
            offset = [-yoffset, -zoffset, xoffset]
            default_offset = np.array([0, -200, 100])
        else:
            offset = [xoffset, yoffset, zoffset]
            default_offset = np.array([100, 0, -200])

        new_actors = []
        for n, (actor, label) in enumerate(zip(actors, labels)):
            if not isinstance(actor, Actor):
                raise ValueError(
                    f"Actor must be an instance of Actor, not {type(actor)}"
                )
            if not isinstance(label, str):
                raise ValueError(f"Label must be a string, not {type(label)}")

            # Get label color
            if color is None:
                color = actor.c()
            elif isinstance(color, (list, tuple)):
                color = color[n]

            # Get mesh's highest point
            points = actor.points().copy()
            point = points[np.argmin(points[:, 1]), :]
            point += np.array(offset) + default_offset

            try:
                if (
                    self.atlas.hemisphere_from_coords(point, as_string=True)
                    == "left"
                ):
                    point = self.atlas.mirror_point_across_hemispheres(point)
            except IndexError:
                pass

            # Create label
            txt = Text(label, point, s=size, c=color)
            new_actors.append(txt)

            # Mark a point on Actor that corresponds to the label location
            if radius is not None:
                pt = actor.closestPoint(point)
                new_actors.append(Sphere(pt, r=radius, c=color))

        # Add to scene and return
        self.add_actor(*new_actors, store=self.actors["labels"])

        return return_list_smart(new_actors)

    def add_line_at_point(self, point, replace_coord, bounds, **kwargs):
        """
            Adds a line oriented on a given axis at a point

            :param point:list or 1d np array with coordinates of point where crosshair is centered
            :param replace_coord: index of the coordinate to replace (i.e. along which axis is the line oriented)
            :param bounds: list of two floats with lower and upper bound for line, determins the extent of the line
            :param kwargs: dictionary with arguments to specify how lines should look like
        """
        # Get line coords
        p0, p1 = point.copy(), point.copy()
        p0[replace_coord] = bounds[0]
        p1[replace_coord] = bounds[1]

        # Get some default params
        color = kwargs.pop("c", "blackboard")
        color = kwargs.pop("color", color)
        lw = kwargs.pop("lw", 3)

        # Create line actor
        act = self.add_actor(Line(p0, p1, c=color, lw=lw, **kwargs))
        return act

    def add_rostrocaudal_line_at_point(self, point, **kwargs):
        """
            Add a line at a point oriented along the trostrocaudal axis

            :param point:list or 1d np array with coordinates of point where crosshair is centered
            :param line_kwargs: dictionary with arguments to specify how lines should look like
        """
        bounds = self.atlas._root_bounds[0]
        return self.add_line_at_point(point, 0, bounds, **kwargs)

    def add_dorsoventral_line_at_point(self, point, **kwargs):
        """
            Add a line at a point oriented along the mdorsoventralediolateral axis

            :param point:list or 1d np array with coordinates of point where crosshair is centered
            :param line_kwargs: dictionary with arguments to specify how lines should look like
        """
        bounds = self.atlas._root_bounds[1]
        return self.add_line_at_point(point, 1, bounds, **kwargs)

    def add_mediolateral_line_at_point(self, point, **kwargs):
        """
            Add a line at a point oriented along the mediolateral axis

            :param point:list or 1d np array with coordinates of point where crosshair is centered
            :param line_kwargs: dictionary with arguments to specify how lines should look like
        """
        bounds = self.atlas._root_bounds[2]
        return self.add_line_at_point(point, 2, bounds, **kwargs)

    def add_crosshair_at_point(
        self,
        point,
        ml=True,
        dv=True,
        ap=True,
        show_point=True,
        line_kwargs={},
        point_kwargs={},
    ):
        """
            Add a crosshair (set of orthogonal lines meeting at a point)
            centered on a given point.

            :param point: list or 1d np array with coordinates of point where crosshair is centered
            :param ml: bool, if True a line oriented on the mediolateral axis is added
            :param dv: bool, if True a line oriented on the dorsoventral axis is added
            :param ap: bool, if True a line oriented on the anteriorposterior or rostsrocaudal axis is added
            :param show_point: bool, if True a sphere at the loation of the point is shown
            :param line_kwargs: dictionary with arguments to specify how lines should look like
            :param point_kwargs: dictionary with arguments to specify how the point should look
        """
        actors = []
        if ml:
            actors.append(
                self.add_mediolateral_line_at_point(point, **line_kwargs)
            )

        if dv:
            actors.append(
                self.add_dorsoventral_line_at_point(point, **line_kwargs)
            )

        if ap:
            actors.append(
                self.add_rostrocaudal_line_at_point(point, **line_kwargs)
            )

        if show_point:
            actors.append(self.add_sphere_at_point(point, **point_kwargs))

        return actors

    def add_plane(self, plane, **kwargs):
        """
            Adds one or more planes to the scene.
            For more details on how to build custom planes, check:
            brainrender/atlases/base.py -> Base.get_plane_at_point 
            method.

            :param plane: either a string with the name of one of 
                the predifined planes ['sagittal', 'coronal', 'horizontal'] 
                or an instance of the Plane class from vedo.shapes
        """
        if isinstance(plane, (list, tuple)):
            planes = plane.copy()
        else:
            planes = [plane]

        actors = []
        for plane in planes:
            if isinstance(plane, str):
                if plane == "sagittal":
                    plane = self.atlas.get_sagittal_plane(**kwargs)
                elif plane == "coronal":
                    plane = self.atlas.get_coronal_plane(**kwargs)
                elif plane == "horizontal":
                    plane = self.atlas.get_horizontal_plane(**kwargs)
                else:
                    raise ValueError(f"Unrecognized plane name: {plane}")
            else:
                if not isinstance(plane, Plane):
                    raise ValueError(
                        "The plane arguments should either be a Plane actor or"
                        + "a string with the name of predefined planes."
                        + f" Not: {plane.__type__}"
                    )
            actors.append(plane)
        self.add_actor(*actors)
        return return_list_smart(actors)

    # ----------------------- Application specific methods ----------------------- #
    def add_probe_from_sharptrack(
        self, probe_points_file, points_kwargs={}, **kwargs
    ):
        """
            Visualises the position of an implanted probe in the brain. 
            Uses the location of points along the probe extracted with SharpTrack
            [https://github.com/cortex-lab/allenCCF].
            It renders the position of points along the probe and a line fit through them.
            Code contributed by @tbslv on github. 

            :param probe_points_file: str, path to a .mat file with probe points coordinates
            :param points_kwargs: dict, used to specify how probe points should look like (e.g color, alpha...)
            :param kwargs: keyword arguments used to specify how the probe should look like (e.g. color, alpha...)
        """
        # Get the position of probe points and render
        probe_points_df = get_probe_points_from_sharptrack(probe_points_file)

        col_by_region = points_kwargs.pop("color_by_region", True)
        color = points_kwargs.pop("color", "salmon")
        radius = points_kwargs.pop("radius", 30)
        spheres = self.add_cells(
            probe_points_df,
            color=color,
            color_by_region=col_by_region,
            res=12,
            radius=radius,
            **points_kwargs,
        )

        # Fit a line through the poitns [adapted from SharpTrack by @tbslv]
        r0 = np.mean(probe_points_df.values, axis=0)
        xyz = probe_points_df.values - r0
        U, S, V = np.linalg.svd(xyz)
        direction = V.T[:, 0]

        # Find intersection with brain surface
        root_mesh = self.atlas._get_structure_mesh("root")
        p0 = direction * np.array([-1]) + r0
        p1 = (
            direction * np.array([-15000]) + r0
        )  # end point way outside of brain, on probe trajectory though
        pts = root_mesh.intersectWithLine(p0, p1)

        # Define top/bottom coordinates to render as a cylinder
        top_coord = pts[0]
        length = np.sqrt(np.sum((probe_points_df.values[-1] - top_coord) ** 2))
        bottom_coord = top_coord + direction * length

        # Render probe as a cylinder
        probe_color = kwargs.pop("color", "blackboard")
        probe_radius = kwargs.pop("radius", 15)
        probe_alpha = kwargs.pop("alpha", 1)

        probe = Cylinder(
            [top_coord, bottom_coord],
            r=probe_radius,
            alpha=probe_alpha,
            c=probe_color,
        )

        # Add to scene
        self.add_actor(probe)
        return probe, spheres

    # ---------------------------------------------------------------------------- #
    #                                   RENDERING                                  #
    # ---------------------------------------------------------------------------- #
    # -------------------------------- Prep render ------------------------------- #
    def apply_render_style(self):
        if brainrender.SHADER_STYLE is None:  # No style to apply
            return

        # Get all actors in the scene
        actors = self.get_actors()

        for actor in actors:
            if actor is not None:
                try:
                    if brainrender.SHADER_STYLE != "cartoon":
                        actor.lighting(style=brainrender.SHADER_STYLE)
                    else:
                        # actor.lighting(style='plastic',
                        # 		enabled=False)
                        actor.lighting("off")
                except:
                    pass  # Some types of actors such as Text 2D don't have this attribute!

    def get_actors(self):
        all_actors = []
        for k, actors in self.actors.items():
            if isinstance(actors, dict):
                if len(actors) == 0:
                    continue
                all_actors.extend(list(actors.values()))
            elif isinstance(actors, list):
                if len(actors) == 0:
                    continue
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
    def render(
        self, interactive=True, video=False, camera=None, zoom=None, **kwargs
    ):
        """
        Takes care of rendering the scene
        """
        self.apply_render_style()

        if not video:
            if (
                not self.jupyter
            ):  # cameras work differently in jupyter notebooks?
                if camera is None:
                    camera = self.camera

                if isinstance(
                    camera, (str, dict)
                ):  # otherwise assume that it's vtk.camera
                    camera = check_camera_param(camera)

                set_camera(self, camera)

            if interactive:
                if self.verbose and not self.jupyter:
                    print(brainrender.INTERACTIVE_MSG)
                elif self.jupyter:
                    print(
                        "The scene is ready to render in your jupyter notebook"
                    )
                else:
                    print("\n\nRendering scene.\n   Press 'q' to Quit")

            self._get_inset()

        if zoom is None and not video:
            if brainrender.WHOLE_SCREEN:
                zoom = 1.85
            else:
                zoom = 1.5

        # Make mesh labels follow the camera
        if not self.jupyter:
            for txt in self.actors["labels"]:
                txt.followCamera(self.plotter.camera)

        self.is_rendered = True
        if not self.jupyter:
            if interactive and not video:
                show(
                    *self.get_actors(),
                    interactive=False,
                    zoom=zoom,
                    bg=brainrender.BACKGROUND_COLOR,
                    axes=self.plotter.axes,
                )
            elif video:
                show(
                    *self.get_actors(),
                    interactive=False,
                    bg=brainrender.BACKGROUND_COLOR,
                    offscreen=True,
                    zoom=zoom,
                    axes=self.plotter.axes,
                )
            else:
                show(
                    *self.get_actors(),
                    interactive=False,
                    offscreen=True,
                    zoom=zoom,
                    bg=brainrender.BACKGROUND_COLOR,
                    axes=self.plotter.axes,
                )

            if interactive and not video:
                show(
                    *self.get_actors(),
                    interactive=True,
                    bg=brainrender.BACKGROUND_COLOR,
                    axes=self.plotter.axes,
                )

    def close(self):
        closePlotter()

    def export_for_web(self, filepath="brexport.html"):
        """
            This function is used to export a brainrender scene
            for hosting it online. It saves an html file that can
            be opened in a web browser to show an interactive brainrender scene
        """
        if not filepath.endswith(".html"):
            raise ValueError("Filepath should point to a .html file")

        # prepare settings
        settings.notebookBackend = "k3d"
        self.jupyter = True
        self.render()

        # Create new plotter and save to file
        plt = Plotter()
        plt.add(self.get_actors())
        plt = plt.show(interactive=False)

        plt.camera[-2] = -1

        print(
            "Ready for exporting. Exporting scenes with many actors might require a few minutes"
        )
        try:
            with open(filepath, "w") as fp:
                fp.write(plt.get_snapshot())
        except:
            raise ValueError(
                "Failed to export scene for web.\n"
                + "Try updating k3d and msgpack: \n "
                + "pip install k3d==2.7.4\n"
                + "pip install -U msgpack"
            )

        print(
            f"The brainrender scene has been exported for web. The results are saved at {filepath}"
        )

        # Reset settings
        settings.notebookBackend = None
        self.jupyter = False

    # ---------------------------------------------------------------------------- #
    #                               USER INTERACTION                               #
    # ---------------------------------------------------------------------------- #
    def keypress(self, key):
        if key == "s":
            if not self.is_rendered:
                print(
                    "You need to render the scene before you can take a screenshot"
                )
                return

            if not os.path.isdir(self.screenshots_folder) and len(
                self.screenshots_folder
            ):
                try:
                    os.mkdir(self.screenshots_folder)
                except Exception as e:
                    raise FileNotFoundError(
                        "Could not crate a folder to save screenshots.\n"
                        + f"Attempted to create a folder at {self.screenshots_folder}"
                        + f"But got exception: {e}"
                    )

            savename = os.path.join(
                self.screenshots_folder, self.screenshots_name
            )
            savename += f'_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'

            if "." not in self.screenshots_extension:
                savename += f".{self.screenshots_extension}"
            else:
                savename += self.screenshots_extension

            print(f"\nSaving screenshots at {savename}\n")
            screenshot(filename=savename, scale=self.screenshots_scale)

    def take_screenshot(self):
        self.keypress("s")


# ---------------------------------------------------------------------------- #
#                                 OTHER SCENES                                 #
# ---------------------------------------------------------------------------- #


class DualScene:
    """ """

    # A class that manages two scenes to display side by side
    def __init__(self, *args, **kwargs):
        self.scenes = [Scene(*args, **kwargs), Scene(*args, **kwargs)]

    def render(self, _interactive=True):
        """ """
        # Create camera and plotter
        if brainrender.WHOLE_SCREEN:
            sz = "full"
        else:
            sz = "auto"

        if brainrender.SHOW_AXES:
            axes = 4
        else:
            axes = 0

        mv = Plotter(
            N=2,
            axes=axes,
            size=sz,
            pos=brainrender.WINDOW_POS,
            bg=brainrender.BACKGROUND_COLOR,
            sharecam=True,
        )

        actors = []
        for scene in self.scenes:
            scene.apply_render_style()
            scene_actors = scene.get_actors()
            actors.append(scene_actors)
            mv.add(scene_actors)

        mv.show(
            actors[0], at=0, zoom=1.15, axes=axes, roll=180, interactive=False
        )
        mv.show(actors[1], at=1, interactive=False)

        if _interactive:
            interactive()

    def close(self):
        closePlotter()


class MultiScene:
    """ """

    def __init__(self, N, scenes=None, *args, **kwargs):
        if scenes is None:
            self.scenes = [Scene(*args, **kwargs) for i in range(N)]
        else:
            if not isinstance(scenes, (list, tuple)):
                raise ValueError("scenes must be a list or a tuple")
            if len(scenes) != N:
                raise ValueError(
                    "Wrong number of scenes passed, it should match N"
                )
            self.scenes = scenes
        self.N = N

    def render(self, _interactive=True, **kwargs):
        """

        :param _interactive:  (Default value = True)
        :param **kwargs:

        """
        camera = kwargs.pop("camera", None)

        for scene in self.scenes:
            scene.apply_render_style()

            if camera is None:
                if scene.atlas.default_camera is None:
                    scene_camera = brainrender.CAMERA
                else:
                    scene_camera = scene.atlas.default_camera
            else:
                if camera:
                    scene_camera = camera
                else:
                    scene_camera = None
            if scene_camera is not None:
                set_camera(scene, scene_camera)

        if self.N > 4:
            print(
                "Rendering {} scenes. Might take a few minutes.".format(self.N)
            )
        mv = Plotter(
            N=self.N,
            axes=4,
            size="auto",
            sharecam=True,
            bg=brainrender.BACKGROUND_COLOR,
        )

        actors = []
        for i, scene in enumerate(self.scenes):
            scene.apply_render_style()
            scene_actors = scene.get_actors()
            actors.append(scene_actors)
            mv.add(scene_actors)

        for i, scene_actors in enumerate(actors):
            mv.show(scene_actors, at=i, interactive=False)

        print("Rendering complete")
        if _interactive:
            interactive()

    def close(self):
        closePlotter()
