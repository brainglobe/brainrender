import pyinspect as pi
from io import StringIO
from rich.console import Console
from pyinspect._colors import orange, mocassin, salmon
import numpy as np

from ._actor import make_actor_label


class Actor(object):
    _needs_label = False  # needs to make a label
    _needs_silhouette = False  # needs to make a silhouette
    _is_transformed = False  # has been transformed to correct axes orientation

    def __init__(self, mesh, name=None, br_class=None, is_text=False):
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
        """
        self.mesh = mesh
        self.name = name
        self.br_class = br_class
        self.is_text = is_text

    def __getattr__(self, attr):
        """
            If an unknown attribute is called, try `self.mesh.attr` 
            to get the meshe's attribute
        """
        if attr == "__rich__":
            return None
        if hasattr(self.__dict__["mesh"], attr):
            return getattr(self.__dict__["mesh"], attr)
        else:  # pragma: no cover
            raise AttributeError(
                f"{self} doesn not have attribute {attr}"
            )  # pragma: no cover

    def __repr__(self):  # pragma: no cover
        return f"brainrender.Actor: {self.name}-{self.br_class}"

    def __str__(self):
        buf = StringIO()
        _console = Console(file=buf, force_jupyter=False)
        _console.print(self)

        return buf.getvalue()

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

        lbls = [Actor.make_actor(l, self.name, "label") for l in labels]
        return lbls

    def make_silhouette(self):
        """
            Create a new silhouette actor outlining this actor
        """
        lw = self._silhouette_kwargs["lw"]
        color = self._silhouette_kwargs["color"]
        sil = self.mesh.silhouette().lw(lw).c(color)

        name = f"{self.name} silhouette"
        sil = Actor.make_actor(sil, name, "silhouette")
        sil._is_transformed = True

        self._needs_silhouette = False

        return sil

    def __rich_console__(self, *args):
        """
            Print some useful characteristics to console.
        """
        rep = pi.Report(
            title=f"[b]brainrender.Actor: ", color=salmon, accent=orange,
        )

        rep.add(f"[b {orange}]name:[/b {orange}][{mocassin}] {self.name}")
        rep.add(f"[b {orange}]type:[/b {orange}][{mocassin}] {self.br_class}")
        rep.line()
        rep.add(
            f"[{orange}]center of mass:[/{orange}][{mocassin}] {self.mesh.centerOfMass().astype(np.int32)}"
        )
        rep.add(
            f"[{orange}]number of vertices:[/{orange}][{mocassin}] {len(self.mesh.points())}"
        )
        rep.add(
            f"[{orange}]dimensions:[/{orange}][{mocassin}] {np.array(self.mesh.bounds()).astype(np.int32)}"
        )
        rep.add(f"[{orange}]color:[/{orange}][{mocassin}] {self.mesh.color()}")

        yield rep
