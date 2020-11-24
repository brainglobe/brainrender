"""
Scene
    - Create a scene, add root and inset if necessary
    - add actor method
    - special methods

"""
import sys
from pathlib import Path
from vedo import Mesh, Plane, Text2D
from vedo import settings as vedo_settings
import pyinspect as pi
from rich import print
from myterial import amber, orange, orange_darker, salmon

from brainrender import settings
from brainrender.atlas import Atlas
from brainrender.render import Render
from brainrender.actor import Actor
from brainrender.actors import Volume
from brainrender._utils import return_list_smart, listify
from brainrender._io import load_mesh_from_file


class Scene(Render):
    def __init__(
        self,
        root=True,
        atlas_name=None,
        inset=True,
        title=None,
        screenshots_folder=None,
    ):
        """
            Main scene in brainrender.
            It coordinates what should be render and how should it look like.

            :param root: bool. If true the brain root mesh is added
            :param atlas_name: str, name of the brainglobe atlas to be used
            :param inset: bool. If true an inset is shown with the brain's outline
            :param title: str. If true a title is added to the top of the window
            :param screenshots_folder: str, Path. Where the screenshots will be saved
        """
        self.actors = []  # stores all actors in the scene
        self.labels = []  # stores all `labels` actors in scene

        self.atlas = Atlas(atlas_name=atlas_name)

        self.screenshots_folder = (
            Path(screenshots_folder)
            if screenshots_folder is not None
            else Path().cwd()
        )
        self.screenshots_folder.mkdir(exist_ok=True)

        # Initialise render class
        Render.__init__(self)

        # Get root mesh
        if root:
            root_alpha = settings.ROOT_ALPHA
        else:
            root_alpha = 0

        self.root = self.add_brain_region(
            "root",
            alpha=root_alpha,
            color=settings.ROOT_COLOR,
            silhouette=True if root else False,
        )
        self.atlas.root = self.root  # give atlas access to root
        self._root_mesh = self.root.mesh.clone()

        # keep track if we need to make an inset
        self.inset = inset

        # add title
        if title:
            self.add(
                Text2D(title, pos=8, s=2.5, c="k", alpha=1, font="Montserrat"),
                name="title",
                br_class="title",
            )

        # keep track if we are in a jupyter notebook
        if vedo_settings.notebookBackend == "k3d":
            self.jupyter = True
        else:
            self.jupyter = False

    def __str__(self):
        return f"A `brainrender.scene.Scene` with {len(self.actors)} actors."

    def __repr__(self):  # pragma: no cover
        return f"A `brainrender.scene.Scene` with {len(self.actors)} actors."

    def __del__(self):
        self.close()

    def _get_inset(self):
        """
            Creates a small inset showing the brain's orientation
        """
        if settings.OFFSCREEN:
            return None

        inset = self._root_mesh.clone()
        inset.alpha(1)  # scale(0.5)
        self.plotter.showInset(inset, pos=(0.95, 0.1), draggable=False)

        if settings.SHADER_STYLE == "cartoon":
            inset.lighting("off")

    def add(self, *items, names=None, classes=None, **kwargs):
        """
            General method to add Actors to the scene.

            :param items: vedo.Mesh, Actor, (str, Path).   
                    If str/path it should be a path to a .obj or .stl file.
                    Whatever the input it's turned into an instance of Actor
                    before adding it to the scne
                
            :param names: names to be assigned to the Actors
            :param classs: br_classes to be assigned to the Actors
            :param **kwargs: parameters to be passed to the individual 
                loading functions (e.g. to load from file and specify the color)
        """
        names = names or ["Actor" for a in items]
        classes = classes or ["None" for a in items]

        # turn items into Actors
        actors = []
        for item, name, _class in zip(items, listify(names), listify(classes)):
            if item is None:
                continue

            if isinstance(item, Mesh):
                actors.append(Actor(item, name=name, br_class=_class))

            elif pi.utils._class_name(item) == "vtkCornerAnnotation":
                # Mark text actors differently because they don't behave like
                # other 3d actors
                actors.append(
                    Actor(item, name=name, br_class=_class, is_text=True)
                )
            elif pi.utils._class_name(item) == "Volume" and not isinstance(
                item, Volume
            ):
                actors.append(
                    Volume(item, name=name, br_class=_class, **kwargs)
                )

            elif isinstance(item, Actor):
                actors.append(item)

            elif isinstance(item, (str, Path)):
                mesh = load_mesh_from_file(item, **kwargs)
                actors.append(Actor(mesh, name=name, br_class=_class))

            else:
                raise ValueError(
                    f"Unrecognized argument: {item} [{pi.utils._class_name(item)}]"
                )

        # Add to the lists actors
        self.actors.extend(actors)
        return return_list_smart(actors)

    def remove(self, *actors):
        """
            Removes actors from the scene.
        """
        for act in actors:
            try:
                self.actors.pop(self.actors.index(act))
            except Exception:
                print(
                    f"Could not remove ({act}, {pi.utils._class_name(act)}) from actors"
                )

    def get_actors(self, name=None, br_class=None):
        """
            Return's the scene's actors that match some search criteria.

            :param name: str or list of str, actors' names
            :param br_class: str or list of str, actors br classes
        """
        matches = self.actors
        if name is not None:
            name = listify(name)
            matches = [m for m in matches if m.name in name]
        if br_class is not None:
            br_class = listify(br_class)
            matches = [m for m in matches if m.br_class in br_class]
        return matches

    def add_brain_region(
        self, *regions, alpha=1, color=None, silhouette=True, hemisphere="both"
    ):
        """
            Dedicated method to add brain regions to render
            
            :param regions: str. String of regions names
            :param alpha: float
            :param color: str. If None the atlas default color is used
            :param silhouette: bool. If true regions Actors will have 
                a silhouette
            :param hemisphere: str.
                - if "both" the complete mesh is returned
                - if "left"/"right" only the corresponding half
                    of the mesh is returned
        """
        # get regions actors from atlas
        regions = self.atlas.get_region(*regions, alpha=alpha, color=color)
        regions = listify(regions) or []

        if hemisphere == "right":
            plane = self.atlas.get_plane(plane="sagittal", norm=(0, 0, -1))
        elif hemisphere == "left":
            plane = self.atlas.get_plane(plane="sagittal", norm=(0, 0, 1))
        if hemisphere in ("left", "right"):
            self.slice(plane, actors=regions, close_actors=True)

        if silhouette and regions and alpha:
            self.add_silhouette(*regions)

        return self.add(*regions)

    def add_silhouette(self, *actors, lw=None, color="k"):
        """
            Dedicated method to add silhouette to actors

            :param actors: Actors
            :param lw: float. Line weight
            :param color: str, silhouette color
        """
        for actor in actors:
            if actor is None:
                continue
            actor._needs_silhouette = True
            actor._silhouette_kwargs = dict(lw=lw or settings.LW, color=color,)

    def add_label(self, actor, label, **kwargs):
        """
            Dedicated method to add lables to actors

            :param actor: Actors
            :param llabelw: str. Text of label
            :param **kwargs: see brainrender._actor.make_actor_label for kwargs
        """
        actor._needs_label = True
        actor._label_str = label
        actor._label_kwargs = kwargs

    def slice(
        self, plane: [str, Plane], actors=None, close_actors=False,
    ):
        """
            Slices actors with a plane.
            
            :param plane: str, Plane. If a string it needs to be 
                a supported plane from brainglobe's atlas api (e.g. 'frontal')
                otherwise it should be a vedo.Plane mesh
            :param actors: list of actors to be sliced. If None all actors
                will be sliced
            :param close_actors: If true the openings in the actors meshes
                caused by teh cut will be closed.
        """
        if self.transform_applied:
            print(
                f"[b {salmon}]Warning: [/b {salmon}][{amber}]you're attempting to cut actors with a plane "
                + "after having rendered the scene, this might give unpredictable results."
                + "\nIt's advised to perform all cuts before the first call to `render`"
            )

        if isinstance(plane, str):
            plane = self.atlas.get_plane(plane=plane)

        actors = actors or self.clean_actors.copy()
        for actor in listify(actors):
            actor.mesh = actor.mesh.cutWithPlane(
                origin=plane.center, normal=plane.normal,
            )
            if close_actors:
                actor.cap()

    @property
    def content(self):
        """
            Prints an overview of the Actors in the scene.
        """

        actors = pi.Report(
            "Scene actors", accent=salmon, dim=orange, color=orange
        )

        for act in self.actors:
            actors.add(
                f"[bold][{amber}]- {act.name}[/bold][{orange_darker}] (type: [{orange}]{act.br_class}[/{orange}]) |[dim] is transformed: [blue]{act._is_transformed}"
            )

        if "win32" != sys.platform:
            actors.print()
        else:
            print(pi.utils.stringify(actors, maxlen=-1))

    @property
    def renderables(self):
        """
            Returns the meshes for all actors.
        """
        if not self.jupyter:
            return [a.mesh for a in self.actors + self.labels]
        else:
            return list(
                set([a.mesh for a in self.actors if not a.is_text])
            )  # pragma: no cover

    @property
    def clean_actors(self):
        """
            returns only ators that are not Text objects and similar
        """
        return [a for a in self.actors if not a.is_text]
