import pyinspect as pi
from io import StringIO
from rich.console import Console
import numpy as np
from myterial import orange, salmon, amber
from vedo import Text3D, Sphere


from brainrender._utils import listify


# transform matrix to fix labels orientation
label_mtx = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def make_actor_label(
    atlas,
    actors,
    labels,
    size=300,
    color=None,
    radius=100,
    xoffset=0,
    yoffset=-500,
    zoffset=0,
):
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
    offset = [-yoffset, -zoffset, xoffset]
    default_offset = np.array([0, -200, 100])

    new_actors = []
    for n, (actor, label) in enumerate(zip(listify(actors), listify(labels))):

        # Get label color
        if color is None:
            color = [0.2, 0.2, 0.2]

        # Get mesh's highest point
        points = actor.mesh.points().copy()
        point = points[np.argmin(points[:, 1]), :]
        point += np.array(offset) + default_offset
        point[2] = -point[2]

        try:
            if atlas.hemisphere_from_coords(point, as_string=True) == "left":
                point = atlas.mirror_point_across_hemispheres(point)
        except IndexError:
            pass

        # Create label
        txt = Text3D(
            label, point * np.array([1, 1, -1]), s=size, c=color, depth=0.1
        )
        new_actors.append(
            txt.rotateX(180, locally=True).rotateY(180, locally=True)
        )

        # Mark a point on Mesh that corresponds to the label location
        if radius is not None:
            pt = actor.closestPoint(point)
            pt[2] = -pt[2]
            sphere = Sphere(pt, r=radius, c=color, res=8)
            sphere.ancor = pt
            new_actors.append(sphere)
            sphere.computeNormals()

    return new_actors


class Actor(object):
    _needs_label = False  # needs to make a label
    _needs_silhouette = False  # needs to make a silhouette
    _is_transformed = False  # has been transformed to correct axes orientation
    _is_added = False  # has the actor been added to the scene already

    labels = []
    silhouette = None

    def __init__(
        self,
        mesh,
        name=None,
        br_class=None,
        is_text=False,
        color=None,
        alpha=None,
    ):
        """
        Actor class representing anythng shown in a brainrender scene.
        Methods in brainrender.actors are used to creates actors specific
        for different data types.

        An actor has a mesh, a name and a brainrender class type.
        It also has methods to create a silhouette or a label.

        :param mesh: instance of vedo.Mesh
        :param name: str, actor name
        :param br_class: str, name of brainrende actors class
        :param is_text: bool, is it a 2d text or annotation?
        :param color: str, name or hex code of color to assign to actor's mesh
        :param alpha: float, transparency to assign to actor's mesh
        """
        self.mesh = mesh
        self.name = name or "Actor"
        self.br_class = br_class or "None"
        self.is_text = is_text

        if color:
            self.mesh.c(color)
        if alpha:
            self.mesh.alpha(alpha)

    def __getattr__(self, attr):
        """
        If an unknown attribute is called, try `self.mesh.attr`
        to get the meshe's attribute
        """
        if "mesh" not in self.__dict__.keys():
            raise AttributeError(
                f"Actor doesn not have attribute {attr}"
            )  # pragma: no cover

        # some attributes should be from .mesh, others from ._mesh
        mesh_attributes = ("centerOfMass",)
        if attr in mesh_attributes:
            if hasattr(self.__dict__["mesh"], attr):
                return getattr(self.__dict__["mesh"], attr)
        else:
            try:
                return getattr(self.__dict__["_mesh"], attr)
            except KeyError:
                # no ._mesh, use .mesh
                if hasattr(self.__dict__["mesh"], attr):
                    return getattr(self.__dict__["mesh"], attr)

        raise AttributeError(
            f"Actor doesn not have attribute {attr}"
        )  # pragma: no cover

    def __repr__(self):  # pragma: no cover
        return f"brainrender.Actor: {self.name}-{self.br_class}"

    def __str__(self):
        buf = StringIO()
        _console = Console(file=buf, force_jupyter=False)
        _console.print(self)

        return buf.getvalue()

    @property
    def center(self):
        """ returns the coordinates of the mesh's center """
        return self.mesh.points().mean(axis=0)

    @classmethod
    def make_actor(cls, mesh, name, br_class):
        """
        Make an actor from a given mesh
        """
        return cls(mesh, name=name, br_class=br_class)

    def make_label(self, atlas):
        """
        Create a new Actor with a sphere and a text
        labelling this actor
        """
        labels = make_actor_label(
            atlas, self, self._label_str, **self._label_kwargs
        )
        self._needs_label = False

        lbls = [
            Actor.make_actor(label, self.name, "label") for label in labels
        ]
        self.labels = lbls
        return lbls

    def make_silhouette(self):
        """
        Create a new silhouette actor outlining this actor
        """
        lw = self._silhouette_kwargs["lw"]
        color = self._silhouette_kwargs["color"]
        sil = self._mesh.silhouette().lw(lw).c(color)

        name = f"{self.name} silhouette"
        sil = Actor.make_actor(sil, name, "silhouette")
        sil._is_transformed = True

        self._needs_silhouette = False
        self.silhouette = sil

        return sil

    def __rich_console__(self, *args):
        """
        Print some useful characteristics to console.
        """
        rep = pi.Report(
            title="[b]brainrender.Actor: ",
            color=salmon,
            accent=orange,
        )

        rep.add(f"[b {orange}]name:[/b {orange}][{amber}] {self.name}")
        rep.add(f"[b {orange}]type:[/b {orange}][{amber}] {self.br_class}")
        rep.line()
        rep.add(
            f"[{orange}]center of mass:[/{orange}][{amber}] {self.mesh.centerOfMass().astype(np.int32)}"
        )
        rep.add(
            f"[{orange}]number of vertices:[/{orange}][{amber}] {len(self.mesh.points())}"
        )
        rep.add(
            f"[{orange}]dimensions:[/{orange}][{amber}] {np.array(self.mesh.bounds()).astype(np.int32)}"
        )
        rep.add(f"[{orange}]color:[/{orange}][{amber}] {self.mesh.color()}")

        yield "\n"
        yield rep
