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
from vedo.shapes import Cylinder, Line
from brainrender.Utils.scene_utils import (
    get_scene_atlas,
    get_cells_colors_from_metadata,
    make_actor_label,
)
from brainrender.Utils.data_io import (
    load_mesh_from_file,
    load_cells_from_file,
)
from brainrender.ABA.aba_utils import parse_sharptrack
from brainrender.Utils.data_manipulation import (
    return_list_smart,
    make_optic_canula_cylinder,
)
from brainrender.Utils.camera import set_camera
from brainrender.Utils.actors_funcs import get_actor_midpoint, get_actor_bounds
from brainrender.render import Render


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

                self.inset = self.root.clone().scale(0.5)
                self.root = None
                self.actors["root"] = None
            else:
                self.inset = self.root.clone().scale(0.5)

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
        # Check arguments
        if isinstance(plane, (list, tuple)):
            planes = plane.copy()
        else:
            planes = [plane]

        if actors is None:
            actors = self.actors
        else:
            if not isinstance(actors, (list, tuple)):
                actors = [actors]

        # Loop over each plane
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
            for actor in actors:
                if actor is None:
                    continue

                try:
                    actor = actor.cutWithPlane(
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

    # ---------------------------------------------------------------------------- #
    #                                POPULATE SCENE                                #
    # ---------------------------------------------------------------------------- #

    def add_root(self, render=True, **kwargs):
        """
        adds the root the scene (i.e. the whole brain outline)

        :param render:  (Default value = True)
        :param **kwargs:

        """
        self.root = self.atlas._get_structure_mesh(
            "root",
            color=brainrender.ROOT_COLOR,
            alpha=brainrender.ROOT_ALPHA,
            **kwargs,
        )
        if self.root is not None:
            self.root.name = "root"
            self.atlas._root_midpoint = get_actor_midpoint(self.root)
            self.atlas._root_bounds = get_actor_bounds(self.root)
        else:
            print("Could not find a root mesh")
            return None

        if render:
            self.actors.append(self.root)

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
            if region in [a.name for a in self.actors if isinstance(a, Mesh)]:
                # Avoid inserting again
                continue

            if add_labels:
                self.add_actor_label(actor, region, **kwargs)

            actor.name = region
            actors.append(actor)

        self.actors.extend(actors)
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

        if isinstance(actors, list):
            for act in actors:
                self.actors.extend(list(act.values()))
        else:
            self.actors.append(list(actors.values()))
        return actors

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
        self.actors.extend(actors)
        return return_list_smart(actors)

    def add_streamlines(self, *args, **kwargs):
        """
        Render streamline data.
        Check the function definition in ABA for more details
        """
        actors = self.atlas.get_streamlines(*args, **kwargs)
        self.actors.extend(actors)
        return return_list_smart(actors)

    # -------------------------- General actors/elements ------------------------- #
    def add_actor(self, *actors, store=None):
        """
        Add a vtk actor to the scene

        :param actor:
        :param store: a list to store added actors

        """
        for actor in actors:
            if store is None:
                self.actors.append(actor)
            else:
                store.append(actor)
        return return_list_smart(actors)

    def add_silhouette(self, *actors, lw=1, color="k", **kwargs):
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
            actor.name = Path(filepath).name
            self.actors.append(actor)
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
        sphere.name = f"sphere {pos}"
        self.actors.append(sphere)
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
        cells_actor.name = name
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
        self.actors.append(spheres)

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
        cylinder = self.add_actor(Cylinder(**params))
        return cylinder

    def add_text(
        self, text, pos=8, size=1.75, color="k", alpha=1, font="Montserrat"
    ):
        """
            Adds a 2D text to the scene. Default params are to crate a large black
            text at the top of the rendering window.

            :param text: str with text to write
            :param kwargs: keyword arguments accepted by vedo.shapes.Text2D
        """

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
        labels = make_actor_label(self.atlas, actors, labels, **kwargs)

        # Add to scene and return
        self.add_actor(*labels, store=self.actors_labels)

        return return_list_smart(labels)

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
        # TODO bgspace could be used here
        axis_dict = dict(rostrocaudal=0, dorsoventral=1, mediolateral=2)
        replace_coord = axis_dict[axis]
        bounds = self.atlas._root_bounds[replace_coord]
        # Get line coords
        p0, p1 = point.copy(), point.copy()
        p0[replace_coord] = bounds[0]
        p1[replace_coord] = bounds[1]

        # Create line actor
        return self.add_actor(Line(p0, p1, c=color, lw=lw, **kwargs))

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
        if isinstance(plane, (list, tuple)):
            planes = plane.copy()
        else:
            planes = [plane]

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
        self.add_actor(*actors)
        return return_list_smart(actors)

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

        self.add_actor(spheres, probe)
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
