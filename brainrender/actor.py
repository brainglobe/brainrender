import pyinspect as pi
from vedo import Mesh
from io import StringIO
from rich.console import Console
from pyinspect._colors import orange, mocassin, salmon
import numpy as np

from brainrender.Utils.scene_utils import make_actor_label


class Actor(Mesh):
    _skip = ["Ruler", "silhouette"]

    _needs_label = False
    _needs_silhouette = False
    _is_transformed = False

    def __init__(self, mesh, name=None, br_class=None):
        self.mesh = mesh
        self.name = name
        self.br_class = br_class

    def __repr__(self):
        return f"brainrender.Actor: {self.name}-{self.br_class}"

    def __str__(self):
        buf = StringIO()
        _console = Console(file=buf, force_jupyter=False)
        _console.print(self)

        return buf.getvalue()

    def __rich_console__(self, *args):
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

    @classmethod
    def make_actor(cls, mesh, name, br_class):
        return cls(mesh, name=name, br_class=br_class)

    def make_label(self, atlas):
        labels = make_actor_label(
            atlas, self, self._label_str, **self._label_kwargs
        )
        self._needs_label = False
        return labels

    def make_silhouette(self):
        lw = self._silhouette_kwargs["lw"]
        color = self._silhouette_kwargs["color"]
        sil = self.mesh.silhouette().lw(lw).c(color)

        name = f"{self.name} silhouette"
        sil = Actor.make_actor(sil, name, "silhoette")
        sil._is_transformed = True

        self._needs_silhouette = False

        return sil
