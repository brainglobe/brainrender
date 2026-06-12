"""Actor class and label utilities for brainrender scenes."""

from __future__ import annotations

from io import StringIO
from typing import Any, Self

import numpy as np
import numpy.typing as npt
import pyinspect as pi
from brainglobe_atlasapi import BrainGlobeAtlas
from brainglobe_space import AnatomicalSpace
from myterial import amber, orange, salmon
from rich.console import Console, ConsoleOptions, RenderResult
from vedo import Mesh, Sphere, Text3D

from brainrender._utils import listify

# transform matrix to fix labels orientation
label_mtx = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def make_actor_label(
    atlas: BrainGlobeAtlas,
    actors: Actor | list[Actor],
    labels: str | list[str],
    size: int = 300,
    color: str | list[float] | None = None,
    radius: int | None = 100,
    xoffset: int = 0,
    yoffset: int = -500,
    zoffset: int = 0,
) -> list[Text3D | Sphere]:
    """
    Create 3D text labels anchored to actor meshes.

    Parameters
    ----------
    atlas
        Atlas used for hemisphere queries and point mirroring.
    actors
        Actors to label.
    labels
        Label string(s) for each actor.
    size
        Text size. Default 300.
    color
        Label colour. Defaults to dark grey if None.
    radius
        Radius of the anchor sphere. Set to None to hide. Default 100.
    xoffset
        Positional offset along x. Default 0.
    yoffset
        Positional offset along y. Default -500.
    zoffset
        Positional offset along z. Default 0.

    Returns
    -------
    list
        Flat list of vedo Text3D and Sphere objects.
    """
    offset = [-yoffset, -zoffset, xoffset]
    default_offset = np.array([0, -200, 100])

    new_actors = []
    for _, (actor, label) in enumerate(zip(listify(actors), listify(labels))):
        # Get label color
        if color is None:
            color = [0.2, 0.2, 0.2]

        # Get mesh's highest point
        points = actor.mesh.vertices.copy()
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
            label, point * np.array([-1, -1, -1]), s=size, c=color, depth=0.1
        )
        new_actors.append(txt.rotate_x(180).rotate_y(180))

        # Mark a point on Mesh that corresponds to the label location
        if radius is not None:
            pt = actor.closest_point(point)
            pt[2] = -pt[2]
            sphere = Sphere(pt, r=radius, c=color, res=8)
            sphere.ancor = pt
            new_actors.append(sphere)
            sphere.compute_normals()

    return new_actors


class Actor:
    """
    Represents any object displayed in a brainrender scene.

    Wraps a vedo Mesh with a name and class type, and provides helpers
    for creating silhouettes and 3D labels. Unknown attribute lookups
    are delegated to the underlying mesh.

    Parameters
    ----------
    mesh
        The 3D mesh for this actor.
    name
        Actor name. Default ``"Actor"``.
    br_class
        Brainrender class type. Default ``"None"``.
    is_text
        Whether this actor is a 2D text annotation. Default False.
    color
        Colour to apply to the mesh on construction.
    alpha
        Transparency to apply to the mesh on construction.
    """

    _needs_label: bool = False  # needs to make a label
    _needs_silhouette: bool = False  # needs to make a silhouette
    _is_transformed: bool = (
        False  # has been transformed to correct axes orientation
    )
    _is_added: bool = False  # has the actor been added to the scene already

    labels: list[Actor] = []
    silhouette: Actor | None = None

    def __init__(
        self,
        mesh: Mesh,
        name: str | None = None,
        br_class: str | None = None,
        is_text: bool = False,
        color: str | None = None,
        alpha: float | None = None,
    ) -> None:
        self.mesh = mesh
        self.name = name or Actor
        self.br_class = br_class or "None"
        self.is_text = is_text

        if color:
            self.mesh.c(color)
        if alpha:
            self.mesh.alpha(alpha)

    def __getattr__(self, attr: str) -> Any:
        """
        Delegate unknown attribute lookups to the underlying mesh.

        Raises
        ------
        AttributeError
            If the attribute is not found on any mesh object.
        """
        if "mesh" not in self.__dict__.keys():
            raise AttributeError(
                f"Actor does not have attribute {attr}"
            )  # pragma: no cover

        # some attributes should be from .mesh, others from ._mesh
        mesh_attributes = ("center_of_mass",)
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
            f"Actor does not have attribute {attr}"
        )  # pragma: no cover

    def __repr__(self) -> str:  # pragma: no cover
        return f"brainrender.Actor: {self.name}-{self.br_class}"

    def __str__(self) -> str:
        buf = StringIO()
        _console = Console(file=buf, force_jupyter=False)
        _console.print(self)

        return buf.getvalue()

    @property
    def center(self) -> npt.NDArray[np.float64]:
        """
        Return the mesh's centre of mass coordinates.

        Returns
        -------
        numpy.ndarray
            Array of shape (3,) with (x, y, z) coordinates.
        """
        return self.mesh.center_of_mass()

    @classmethod
    def make_actor(cls, mesh: Mesh, name: str, br_class: str) -> Self:
        """
        Construct an Actor from an existing mesh.

        Parameters
        ----------
        mesh
            Mesh to wrap.
        name
            Actor name.
        br_class
            Brainrender class type.

        Returns
        -------
        Actor
        """
        return cls(mesh, name=name, br_class=br_class)

    def make_label(self, atlas: BrainGlobeAtlas) -> list[Actor]:
        """
        Create 3D label actors anchored to this actor's mesh.

        Parameters
        ----------
        atlas
            Atlas used for hemisphere queries and mirroring.

        Returns
        -------
        list of Actor
            Label actors (text and optional sphere markers).
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

    def make_silhouette(self) -> Actor:
        """
        Create a silhouette actor outlining this actor's mesh.

        Returns
        -------
        Actor
            Silhouette actor with brainrender class ``"silhouette"``.
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

    def mirror(
        self,
        axis: str,
        origin: npt.NDArray | None = None,
        atlas: BrainGlobeAtlas | None = None,
    ) -> None:
        """
        Mirror the actor's mesh across the given axis.

        Accepts Cartesian axes (``'x'``, ``'y'``, ``'z'``) or anatomical
        plane names (``'sagittal'``, ``'vertical'``, ``'frontal'``).
        If an anatomical name is used without an atlas, ``'asr'`` space
        is assumed. The mesh is updated in place.

        Parameters
        ----------
        axis
            Axis or anatomical plane to mirror across.
        origin
            Centre of the mirroring operation. Default None.
        atlas
            Atlas used to resolve anatomical axis names. Default None.
        """
        if axis in ["sagittal", "vertical", "frontal"]:
            anatomical_space = atlas.space if atlas else AnatomicalSpace("asr")

            axis_ind = anatomical_space.get_axis_idx(axis)
            axis = "x" if axis_ind == 0 else "y" if axis_ind == 1 else "z"

        self.mesh = self.mesh.mirror(axis, origin)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
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
            f"[{orange}]center of mass:[/{orange}][{amber}] {self.mesh.center_of_mass().astype(np.int32)}"
        )
        rep.add(
            f"[{orange}]number of vertices:[/{orange}][{amber}] {self.mesh.npoints}"
        )
        rep.add(
            f"[{orange}]dimensions:[/{orange}][{amber}] {np.array(self.mesh.bounds()).astype(np.int32)}"
        )
        rep.add(f"[{orange}]color:[/{orange}][{amber}] {self.mesh.color()}")

        yield "\n"
        yield rep
