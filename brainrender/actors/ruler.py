"""Ruler actors for measuring distances in brainrender scenes."""

import numpy as np
import numpy.typing as npt
from loguru import logger
from vedo import merge
from vedo.shapes import Line, Sphere, Text3D
from vedo.utils import mag, precision

from brainrender.actor import Actor


def ruler(
    p1: npt.ArrayLike,
    p2: npt.ArrayLike,
    unit_scale: float = 1,
    units: str | None = None,
    s: float = 50,
) -> Actor:
    """
    Create a ruler showing the distance between two points.
    The ruler is composed of a line between the points and
    a text indicating the distance.

    Parameters
    ----------
    p1
        Coordinates of the first point.
    p2
        Coordinates of the second point.
    unit_scale
        Scale factor for the displayed units (e.g. 0.001 to show mm instead of µm).
    units
        Unit label string (e.g. ``"mm"``).
    s
        Text size. Default 50.

    Returns
    -------
    Actor
        A ruler actor showing the distance between the two points.
    """
    logger.debug(f"Creating a ruler actor between {p1} and {p2}")
    actors = []

    # Make two line segments
    midpoint = np.array([(x + y) / 2 for x, y in zip(p1, p2)])
    gap1 = ((midpoint - p1) * 0.8) + p1
    gap2 = ((midpoint - p2) * 0.8) + p2

    actors.append(Line(p1, gap1, lw=200))
    actors.append(Line(gap2, p2, lw=200))

    # Add label
    if units is None:  # pragma: no cover
        units = ""  # pragma: no cover
    dist = mag(p2 - p1) * unit_scale
    label = precision(dist, 3) + " " + units
    lbl = Text3D(label, pos=midpoint, s=s + 100, justify="center")
    lbl.rotate_z(180, around=midpoint)
    actors.append(lbl)

    # Add spheres add end
    actors.append(Sphere(p1, r=s, c=[0.3, 0.3, 0.3]))
    actors.append(Sphere(p2, r=s, c=[0.3, 0.3, 0.3]))

    act = Actor(merge(*actors), name="Ruler", br_class="Ruler")
    act.c((0.3, 0.3, 0.3)).alpha(1).lw(2)

    return act


def ruler_from_surface(
    p1: npt.ArrayLike,
    root: Actor,
    unit_scale: float = 1,
    axis: int = 1,
    units: str | None = None,
    s: float = 50,
) -> Actor:
    """
    Create a ruler between a point and the brain's surface.

    Parameters
    ----------
    p1
        Coordinates of the point.
    root
        Actor with the brain's root mesh.
    unit_scale
        Scale factor for the displayed units (e.g. 0.001 to show mm instead of µm).
    axis
        Index of the axis along which the distance is computed. Default 1.
    units
        Unit label string (e.g. ``"mm"``).
    s
        Text size. Default 50.

    Returns
    -------
    Actor
        A ruler actor showing the distance from the point to the brain surface.
    """
    logger.debug(f"Creating a ruler actor between {p1} and brain surface")
    # Get point on brain surface
    p2 = p1.copy()
    p2[axis] = 0  # zero the chosen coordinate

    pts = root.mesh.intersect_with_line(p1, p2)
    surface_point = pts[0]

    return ruler(p1, surface_point, unit_scale=unit_scale, units=units, s=s)
