"""
Scene
    - Create a scene, add root and inset if necessary
    - add actor method
    - special methods

"""
import sys
from pathlib import Path
from vedo import Mesh, Plane, Sphere, Text2D
from vedo import settings as vedo_settings
import pyinspect as pi
from rich import print


from brainrender import settings
from .atlas import Atlas
from .render import Render
from .actor import Actor
from ._utils import return_list_smart, listify
from ._io import load_mesh_from_file
from ._colors import mocassin, orange, dimorange, salmon


class Scene(Render):
    actors = []  # stores all actors in the scene
    labels = []  # stores all `labels` actors in scene

    def __init__(
        self,
        root=True,
        atlas_name=None,
        inset=True,
        title=None,
        screenshots_folder=None,
    ):
        self.atlas = Atlas(atlas_name=atlas_name)

        self.screenshots_folder = (
            Path(screenshots_folder)
            if screenshots_folder is not None
            else Path().cwd()
        )
        self.screenshots_folder.mkdir(exist_ok=True)

        Render.__init__(self)

        if root:
            self.root = self.add_brain_region(
                "root", alpha=settings.ROOT_ALPHA, color=settings.ROOT_COLOR
            )
        else:
            self.root = self.atlas.get(
                "region", "root", alpha=0, color=settings.ROOT_COLOR
            )
        self.atlas.root = self.root  # give atlas access to root

        self.inset = (
            inset  # the inset will be created when the scene is first rendered
        )

        if title:
            self.add(
                Text2D(title, pos=8, s=2.5, c="k", alpha=1, font="Montserrat"),
                name="title",
                br_class="title",
            )

        if vedo_settings.notebookBackend == "k3d":
            self.jupyter = True
        else:
            self.jupyter = False

    def __str__(self):
        return f"A `brainrender.scene.Scene` with {len(self.actors)} actors."

    def __repr__(self):
        return f"A `brainrender.scene.Scene` with {len(self.actors)} actors."

    def __del__(self):
        self.close()

    def _get_inset(self):
        inset = self.root.mesh.clone()
        inset.scale(0.5).alpha(1)
        self.plotter.showInset(inset, pos=(0.95, 0.1), draggable=False)

        if settings.SHADER_STYLE == "cartoon":
            self.plotter.showInset(
                inset.silhouette().lw(0.5).c("k"),
                pos=(0.95, 0.1),
                draggable=False,
            )

    def add(self, *items, names=None, classes=None, **kwargs):
        names = names or ["Actor" for a in items]
        classes = classes or ["None" for a in items]

        # Should deal with Mesh, Actor or filepath
        actors = []
        for item, name, _class in zip(items, listify(names), listify(classes)):
            if item is None:
                continue
            if isinstance(item, Mesh):
                actors.append(Actor(item, name=name, br_class=_class))
            elif pi.utils._class_name(item) == "vtkCornerAnnotation":
                actors.append(
                    Actor(item, name=name, br_class=_class, is_text=True)
                )
            elif isinstance(item, Actor):
                actors.append(item)

            elif isinstance(item, (str, Path)):
                mesh = load_mesh_from_file(item, **kwargs)
                actors.append(Actor(mesh, name=name, br_class=_class))

            else:
                raise ValueError(f"Unrecognized argument: {item}")

        self.actors.extend(actors)
        return return_list_smart(actors)

    def add_point(self, pos, radius=100, color="blackboard", alpha=1, res=25):
        self.add(
            Sphere(pos=pos, r=radius, c=color, alpha=alpha, res=res),
            names="point",
            classes="point",
        )

    def add_brain_region(
        self, *regions, alpha=1, color=None, silhouette=True, hemisphere="both"
    ):
        regions = self.atlas.get("region", *regions, alpha=alpha, color=color)
        regions = listify(regions) or []

        if hemisphere == "right":
            plane = self.atlas.get_plane(plane="sagittal", norm=(0, 0, -1))
        elif hemisphere == "left":
            plane = self.atlas.get_plane(plane="sagittal", norm=(0, 0, 1))
        if hemisphere in ("left", "right"):
            self.slice(plane, actors=regions, close_actors=True)

        if silhouette and regions:
            self.add_silhouette(*regions)

        return self.add(*regions)

    def add_silhouette(self, *actors, lw=2, color="k"):
        for actor in actors:
            if actor is None:
                continue
            actor._needs_silhouette = True
            actor._silhouette_kwargs = dict(lw=lw, color=color,)

    def add_label(self, actor, label, **kwargs):
        actor._needs_label = True
        actor._label_str = label
        actor._label_kwargs = kwargs

    def slice(
        self, plane: [str, Plane], actors=None, close_actors=False,
    ):
        if self.transform_applied:
            print(
                f"[b {salmon}]Warning: [/b {salmon}][{mocassin}]you're attempting to cut actors with a plane "
                + "after having rendered the scene at lest once, this might give unpredicable results."
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
        actors = pi.Report(
            "Scene actors", accent=salmon, dim=orange, color=orange
        )

        for act in self.actors:
            actors.add(
                f"[bold][{mocassin}]- {act.name}[/bold][{dimorange}] (type: [{orange}]{act.br_class}[/{orange}]) |[dim] is transformed: [blue]{act._is_transformed}"
            )

        if "win" not in sys.platform:
            actors.print()
        else:
            print(pi.utils.stringify(actors, maxlen=-1))

    @property
    def renderables(self):
        if not self.jupyter:
            return [a.mesh for a in self.actors + self.labels]
        else:
            return list(set([a.mesh for a in self.actors if not a.is_text]))

    @property
    def clean_actors(self):
        """
            returns only ators that are not Text objects and similar
        """
        return [a for a in self.actors if not a.is_text]
