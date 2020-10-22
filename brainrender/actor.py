import pyinspect as pi
from vedo import Mesh
from io import StringIO
from rich.console import Console
from pyinspect._colors import orange, mocassin, salmon
import numpy as np


class Actor(Mesh):
    _skip = ["Ruler", "silhouette"]

    def __init__(self, mesh, name=None, br_class=None):
        try:
            if mesh.name not in self._skip:
                Mesh.__init__(self, inputobj=[mesh.points(), mesh.faces()])
            else:
                raise AttributeError
        except AttributeError:
            raise ValueError(f"Failed to create Actor from {str(type(mesh))}")
        else:
            self.c(mesh.c())
            self.alpha(mesh.alpha())

            self.name = name
            self.br_class = br_class
            self._is_transformed = False

            if name == "label text":
                self._original_actor = mesh._original_actor
                self._label = mesh._label
                self._kwargs = mesh._kwargs

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
            f"[{orange}]center of mass:[/{orange}][{mocassin}] {self.centerOfMass().astype(np.int32)}"
        )
        rep.add(
            f"[{orange}]number of vertices:[/{orange}][{mocassin}] {len(self.points())}"
        )
        rep.add(
            f"[{orange}]dimensions:[/{orange}][{mocassin}] {np.array(self.bounds()).astype(np.int32)}"
        )
        rep.add(f"[{orange}]color:[/{orange}][{mocassin}] {self.color()}")

        yield rep
