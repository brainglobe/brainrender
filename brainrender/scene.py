import brainrender
from pathlib import Path
from vedo import (
    Plotter,
    shapes,
    interactive,
    Text2D,
    closePlotter,
    Plane,
    Mesh,
)
import numpy as np
import pyinspect as pi
from pyinspect._colors import dimorange, orange, mocassin, salmon
from rich import print as rprint
import sys

from brainrender.Utils.scene_utils import (
    get_scene_atlas,
    get_cells_colors_from_metadata,
    parse_add_actors_inputs,
)
from brainrender.Utils.data_io import (
    load_mesh_from_file,
    load_cells_from_file,
)
from brainrender.ABA.aba_utils import parse_sharptrack
from brainrender.Utils.data_manipulation import (
    return_list_smart,
    make_optic_canula_cylinder,
    listify,
)
from brainrender.Utils.camera import set_camera
from brainrender.Utils.actors_funcs import get_actor_midpoint, get_actor_bounds
from brainrender.render import Render
from brainrender.Utils.ruler import ruler
from brainrender.actor import Actor


class Scene(Render):
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
        add_root=None,
        verbose=True,
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
            :param atlas: str, class. Default None. If a string is passed it whould be the name of a valide
                brainglobe_api atlas. Alternative a class object can be passed, this should support the functionality
                expected of an atlas class. 
                if no atlas is passed the allen brain atlas for the adult mouse brain is used. If a string with the atlas
                name is passed it will try to load the corresponding brainglobe atlas.
            :param atlas_kwargs: dictionary used to pass extra arguments to atlas class
        """
        # Get atlas
        self.atlas = get_scene_atlas(atlas, base_dir, atlas_kwargs, **kwargs)

        # Initialise Render
        Render.__init__(
            self,
            verbose,
            display_inset,
            camera,
            screenshot_kwargs,
            use_default_key_bindings,
        )

        # Prepare store for actors added to scene
        self.actors = []
        self.actors_labels = []
        self.store = {}  # in case we need to store some data

        # Add items to scene
        if add_root is None:
            add_root = brainrender.DISPLAY_ROOT
        self.add_root(render=add_root)

        if title is not None:
            self.add_text(title)

        # Placeholder variables
        self.inset = None  # the first time the scene is rendered create and store the inset here
        self.is_rendered = False  # keep track if scene has been rendered

    def __str__(self):
        return f"A `brainrender.scene.Scene` with {len(self)} actors."

    def __repr__(self):
        return f"A `brainrender.scene.Scene` with {len(self)} actors."

    def __add__(self, other):
        if isinstance(other, Mesh):
            self.add_actor(other)
        elif isinstance(other, (Path, str)):
            self.add_from_file(str(other))
        else:
            raise ValueError(f"Can't add object {other} to scene")

    def __iadd__(self, other):
        self.__add__(other)
        return self

    def __len__(self):
        return len(self.actors)

    def __getitem__(self, index):
        return self.actors[index]

    def __del__(self):
        self.close()

    # ---------------------------------------------------------------------------- #
    #                                     Utils                                    #
    # ---------------------------------------------------------------------------- #

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

                self.inset = self.root.mesh.clone().scale(0.5)
                self.root = None
            else:
                self.inset = self.root.mesh.clone().scale(0.5)

            self.inset.alpha(1)
            self.plotter.showInset(
                self.inset, pos=(0.95, 0.1), draggable=False
            )

    def cut_actors_with_plane(
        self,
        plane,
        actors=None,
        showplane=False,
        returncut=False,
        close_actors=False,
        **kwargs,
    ):
        if self.transform_applied:
            rprint(
                f"[b {salmon}]Warning: [/b {salmon}][{mocassin}]you're attempting to cut actors with a plane "
                + "after having rendered the scene at lest once, this might give unpredicable results."
                + "\nIt's advised to perform all cuts before the first call to `render`"
            )
        # Loop over each plane
        planes = listify(plane).copy()
        to_return = []
        for plane in planes:
            # Get the plane actor
            if isinstance(plane, str):
                plane = self.atlas.get_plane_at_point(plane=plane, **kwargs)
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
            if actors is None:
                actors = self.actors.copy()

            for actor in listify(actors):
                if actor is None:
                    continue

                try:
                    actor.mesh = actor.mesh.cutWithPlane(
                        origin=plane.center,
                        normal=plane.normal,
                        returnCut=returncut,
                    )
                except AttributeError:
                    # some rendered objects can't be cut (e.g.text 2d)
                    continue

                if returncut:
                    to_return.append(actor)

                if close_actors:
                    actor.cap()

        if len(to_return) == 1:
            return to_return[0]
        else:
            return to_return

    def list_actors(self, extensive=False):
        actors = pi.Report(
            "Scene actors", accent=salmon, dim=orange, color=orange
        )

        for act in self.actors + self.actors_labels:
            try:
                name = f"[b]{act.name}"

                if name is None:
                    name = str(act)

            except AttributeError:
                name = "noname"

            try:
                br_class = act.br_class
            except AttributeError:
                if isinstance(act, Actor):
                    print(
                        f'Actor {name} does not have a "br_class" attribute!\n{act}'
                    )
                else:
                    continue

            if not extensive:
                actors.add(
                    f"[b {mocassin}]- {name}[/b][{dimorange}] (type: [{orange}]{br_class}[/{orange}])"
                )
            else:
                actors.add(
                    f"[b {mocassin}]- {name}[/b][{dimorange}] (type: [{orange}]{br_class}[/{orange}]) | is transformed: [blue]{act._is_transformed}"
                )

        if "win" not in sys.platform:
            actors.print()
        else:
            print(pi.utils.stringify(actors, maxlen=-1))

    # ---------------------------------------------------------------------------- #
    #                                POPULATE SCENE                                #
    # ---------------------------------------------------------------------------- #

    def add_actor(self, *actors, name=None, br_class=None, store=None):
        """
        Add a vtk actor to the scene

        :param actor:
        :param store: a list to store added actors

        """
        # Parse inputs to match a name and br class to each actor
        actors, names, br_classes = parse_add_actors_inputs(
            actors, name, br_class
        )

        # Add actors to scene
        to_return = []
        for actor, name, br_class in zip(actors, names, br_classes):
            for act in listify(actor):
                if act is None:
                    continue

                try:
                    act = Actor(act, name=name, br_class=br_class)
                except Exception:  # doesn't work for annotations
                    act.name = name
                    act.br_class = br_class
                    act._is_transformed = False

                if store is None:
                    self.actors.append(act)
                else:
                    store.append(act)
                to_return.append(act)

        return return_list_smart(to_return)

    def add_root(self, render=True, **kwargs):
        """
        adds the root the scene (i.e. the whole brain outline)

        :param render:  (Default value = True)
        :param **kwargs:

        """
        root = self.atlas._get_structure_mesh(
            "root",
            color=brainrender.ROOT_COLOR,
            alpha=brainrender.ROOT_ALPHA,
            **kwargs,
        )

        if root is not None:
            self.atlas._root_midpoint = get_actor_midpoint(root)
            self.atlas._root_bounds = get_actor_bounds(root)

        else:
            print("Could not find a root mesh")
            return None

        if render:
            self.root = self.add_actor(root, name="root", br_class="root")

        elif brainrender.SHOW_AXES:
            # if showing axes, add a transparent root
            # so that scene has right scale
            root.alpha(0)
            self.root = self.add_actor(root, name="root", br_class="root")
        else:
            self.root = root.alpha(0)

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
            if region in [a.name for a in self.actors if isinstance(a, Actor)]:
                # Avoid inserting again
                continue

            if add_labels:
                self.add_actor_label(actor, region, **kwargs)

            act = self.add_actor(actor, name=region, br_class="brain region")
            actors.append(act)

        return return_list_smart(actors)

    def add_neurons(self, *args, **kwargs):
        """
        Adds rendered morphological data of neurons reconstructions.
        Check the atlas' method to know how it works
        """
        actors, store = self.atlas.get_neurons(*args, **kwargs)

        if store is not None:
            for n, v in store.items():
                self.store[n] = v

        to_return = []
        for act in listify(actors):
            if isinstance(act, dict):
                act = self.add_actor(
                    list(act.values()), name="neuron", br_class="neuron"
                )
                to_return.append(act)
            else:
                act = self.add_actor(
                    list(actors), name="neuron", br_class="neuron"
                )
                to_return.append(act)
        return to_return

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
            self.add_actor(actor, name="synapses", br_class="synapses")

    def add_tractography(self, *args, **kwargs):
        """
        Renders tractography data and adds it to the scene. 
        Check the function definition in ABA for more details
        """

        actors = self.atlas.get_tractography(*args, **kwargs)
        for act in actors:
            self.add_actor(
                actors, name="tractography", br_class="tractography"
            )
        return return_list_smart(actors)

    def add_streamlines(self, *args, **kwargs):
        """
        Render streamline data.
        Check the function definition in ABA for more details
        """
        actors = self.atlas.get_streamlines(*args, **kwargs)
        for act in actors:
            self.add_actor(actors, name="streamlines", br_class="streamlines")
        return return_list_smart(actors)

    # -------------------------- General actors/elements ------------------------- #

    def add_silhouette(self, *actors, lw=1, color="k"):
        """
            Add a silhouette around a given Actor. 
            Note, this function doesn't actually create the silhouette, 
            that's done after the actor is rendered.

            :param actors: instances of Actor class
            :param lw: float, line weight, width of silhouette
            :oaram color: color of silhouette line
        """
        for act in actors:
            act._needs_silhouette = True
            act._silhouette_kwargs = dict(lw=lw, color=color,)

    def add_from_file(self, *filepaths, **kwargs):
        """
        Add data to the scene by loading them from a file. Should handle .obj, .vtk and .nii files.

        :param filepaths: path to the file. Can pass as many arguments as needed
        :param **kwargs:

        """
        actors = []
        for filepath in filepaths:
            actor = load_mesh_from_file(filepath, **kwargs)
            name = Path(filepath).name
            act = self.add_actor(actor, name=name, br_class=name)
            actors.append(act)
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
        sphere = self.add_actor(
            sphere,
            name=f"sphere [{orange}]at {np.array(pos).astype(np.int32)}",
            br_class="sphere",
        )
        return sphere

    def add_cells_from_file(
        self, filepath, hdf_key="hdf", color="red", radius=25, res=7, alpha=1
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
        # Load cells
        cells, name = load_cells_from_file(filepath, hdf_key=hdf_key)

        # Render cells
        cells_actor = self.add_cells(
            cells, color=color, radius=radius, res=res, alpha=alpha
        )
        return cells_actor

    def add_cells(
        self,
        coords,
        color="red",
        color_by_region=False,
        color_by_metadata=None,
        radius=25,
        res=7,
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
        coords_df = coords.copy()  # keep a copy
        if col_names is None:
            col_names = ["x", "y", "z"]

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

        # Update color
        if color_by_region:
            color = self.atlas.get_colors_from_coordinates(coords)
        elif color_by_metadata is not None:
            color = get_cells_colors_from_metadata(
                color_by_metadata, coords_df, color
            )

        # Create actors
        spheres = shapes.Spheres(
            coords, c=color, r=radius, res=res, alpha=alpha
        )
        spheres = self.add_actor(spheres, name="cells", br_class="cells")

        if verbose:
            print("Added {} cells to the scene".format(len(coords)))

        return spheres

    def add_optic_cannula(
        self, *args, **kwargs,
    ):
        """
            Adds a cylindrical vedo actor to scene to render optic cannulas. By default
            this is a semi-transparent blue cylinder centered on the center of mass of
            a specified target region and oriented vertically. Parameters are specified 
            as keyword arguments.

            :param target_region: str, acronym of target region to extract coordinates
                of implanted fiber. By defualt the fiber will be centered on the center
                of mass of the target region but the offset arguments can be used to
                fine tune the position. Alternative pass a 'pos' argument with AP-DV-ML coords.
            :param pos: list or tuple or np.array with X,Y,Z coordinates. Must have length = 3.
            :param x_offset, y_offset, z_offset: int, used to fine tune the coordinates of 
                the implanted cannula.
            :param **kwargs: used to specify which hemisphere the cannula is and parameters
                of the rendered cylinder: color, alpha, rotation axis...
        """

        # Compute params
        params = make_optic_canula_cylinder(
            self.atlas, self.root, *args, **kwargs
        )

        # Create actor
        cylinder = self.add_actor(
            shapes.Cylinder(**params),
            name="optic cannula",
            br_class="optic cannula",
        )
        return cylinder

    def add_text(
        self, text, pos=8, size=2.5, color="k", alpha=1, font="Montserrat"
    ):
        """
            Adds a 2D text to the scene. Default params are to crate a large black
            text at the top of the rendering window.

            :param text: str with text to write
            :param kwargs: keyword arguments accepted by vedo.shapes.Text2D
        """

        txt = self.add_actor(
            Text2D(text, pos=pos, s=size, c=color, alpha=alpha, font=font),
            name="text",
            br_class="text",
        )
        return txt

    def add_actor_label(self, actors, labels, **kwargs):
        """
            Prepares an actor label. Labels are only created when
            `Scene.render` is called. 

            :param kwargs: key word arguments can be passed to determine 
                    text appearance and location:
                        - size: int, text size. Default 300
                        - color: str, text color. A list of colors can be passed
                                if None the actor's color is used. Default None.
                        - xoffset, yoffset, zoffset: integers that shift the label position
                        - radius: radius of sphere used to denote label anchor. Set to 0 or None to hide. 
        """
        for actor, label in zip(listify(actors), listify(labels)):
            actor._needs_label = True
            actor._label_str = label
            actor._label_kwargs = kwargs

    def add_line_at_point(
        self, point, axis, color="blackboard", lw=3, **kwargs
    ):
        """
            Adds a line oriented on a given axis at a point

            :param point:list or 1d np array with coordinates of point where crosshair is centered
            :param replace_coord: index of the coordinate to replace (i.e. along which axis is the line oriented)
            :param bounds: list of two floats with lower and upper bound for line, determins the extent of the line
            :param kwargs: dictionary with arguments to specify how lines should look like
        """
        axis_dict = dict(rostrocaudal=0, dorsoventral=1, mediolateral=2)
        replace_coord = axis_dict[axis]
        bounds = self.atlas._root_bounds[replace_coord]
        # Get line coords
        p0, p1 = point.copy(), point.copy()
        p0[replace_coord] = bounds[0]
        p1[replace_coord] = bounds[1]

        # Create line actor
        line = shapes.Line(p0, p1, c=color, lw=lw, **kwargs)
        return self.add_actor(
            line,
            name=f"line through {point.astype(np.int32)}",
            br_class="line",
        )

    def add_crosshair_at_point(
        self, point, show_point=True, line_kwargs={}, point_kwargs={},
    ):
        """
            Add a crosshair (set of orthogonal lines meeting at a point)
            centered on a given point.

            :param point: list or 1d np array with coordinates of point where crosshair is centered
            :param show_point: bool, if True a sphere at the loation of the point is shown
            :param line_kwargs: dictionary with arguments to specify how lines should look like
            :param point_kwargs: dictionary with arguments to specify how the point should look
        """
        return [
            self.add_line_at_point(point, ax, **line_kwargs)
            for ax in ["rostrocaudal", "dorsoventral", "mediolateral"]
        ]

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
        if self.transform_applied:
            rprint(
                f"[b {salmon}]Warning: [/b {salmon}][{mocassin}]you're attempting to add a plane "
                + "after having rendered the scene at lest once, this might give unpredicable results."
                + "\nIt's advised to perform add all planes before the first call to `render`"
            )

        planes = listify(plane).copy()
        actors = []
        for plane in planes:
            if isinstance(plane, str):
                plane = self.atlas.get_plane_at_point(plane=plane, **kwargs)
            else:
                if not isinstance(plane, Plane):
                    raise ValueError(
                        "The plane arguments should either be a Plane actor or"
                        + "a string with the name of predefined planes."
                        + f" Not: {plane.__type__}"
                    )

            actors.append(plane)

        self.add_actor(*actors, name="plane", br_class="plane")
        return return_list_smart(actors)

    def add_ruler_from_surface(self, p0, unit_scale=1, axis=1):
        """
            Given a point, this function adds a ruler object showing
            the distance of that point from the brain surface along a
            given axis.

            :param p0: np.array with point coordinates
            :param axis: int, index of the axis along
                    which to measure distance
        """
        # Get point on brain surface
        p1 = p0.copy()
        p1[axis] = 0  # zero the choosen coordinate

        pts = self.root.mesh.intersectWithLine(p0, p1)
        surface_point = pts[0]

        # create ruler
        return self.add_actor(
            ruler(surface_point, p0, unit_scale=unit_scale, units="mm",),
            name=f"ruler [{orange}]through {p0.astype(np.int32)}",
            br_class="ruler",
        )

    # ----------------------- Application specific methods ----------------------- #

    def add_probe_from_sharptrack(
        self, probe_points_file, points_kwargs={}, name=None, **kwargs
    ):
        """
            Visualises the position of an implanted probe in the brain. 
            Uses the location of points along the probe extracted with SharpTrack
            [https://github.com/cortex-lab/allenCCF].
            It renders the position of points along the probe and a line fit through them.
            Code contributed by @tbslv on github. 

            :param probe_points_file: str, path to a .mat file with probe points coordinates
            :param kwargs: keyword arguments used to specify how the probe and the poitns 
                                should look like (e.g. color, alpha...)
        """
        probe_points_df, points_params, probe, color = parse_sharptrack(
            self.atlas, probe_points_file, name, **kwargs
        )

        spheres = self.add_cells(probe_points_df, **points_params)
        self.add_actor(
            spheres,
            probe,
            name=["probe points", "probe"],
            br_class="sharptrack track",
        )
        return probe, spheres


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
        mv = Plotter(
            N=2,
            axes=4 if brainrender.SHOW_AXES else 0,
            size="full" if brainrender.WHOLE_SCREEN else "auto",
            pos=brainrender.WINDOW_POS,
            bg=brainrender.BACKGROUND_COLOR,
            sharecam=True,
        )

        actors = []
        for scene in self.scenes:
            scene.apply_render_style()
            actors.append(scene.actors)
            mv.add(scene.actors)

        mv.show(
            actors[0],
            at=0,
            zoom=1.15,
            axes=4 if brainrender.SHOW_AXES else 0,
            roll=180,
            interactive=False,
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

        mv = Plotter(
            N=self.N,
            axes=4 if brainrender.SHOW_AXES else 0,
            size="full" if brainrender.WHOLE_SCREEN else "auto",
            sharecam=True,
            bg=brainrender.BACKGROUND_COLOR,
        )

        actors = []
        for i, scene in enumerate(self.scenes):
            scene.apply_render_style()
            actors.append(scene.actors)
            mv.add(scene.actors)

        for i, scene.actors in enumerate(actors):
            mv.show(scene.actors, at=i, interactive=False)

        print("Rendering complete")
        if _interactive:
            interactive()

    def close(self):
        closePlotter()
