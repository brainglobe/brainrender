import numpy as np
from loguru import logger

from vedo import merge
from vedo.shapes import Line, Sphere, Text3D
from vedo.utils import precision, mag

from brainrender.actor import Actor


def ruler(p1, p2, unit_scale=1, units=None, s=50):
    """
    Creates a ruler showing the distance between two points.
    The ruler is composed of a line between the points and
    a text indicating the distance.

    :param p1: list, np.ndarray with coordinates of first point
    :param p2: list, np.ndarray with coordinates of second point
    :param unit_scale: float. To scale the units (e.g. show mm instead of µm)
    :param units: str, name of unit (e.g. 'mm')
    :param s: float size of text

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
    lbl.SetOrientation([0, 0, 180])
    actors.append(lbl)

    # Add spheres add end
    actors.append(Sphere(p1, r=s, c=[0.3, 0.3, 0.3]))
    actors.append(Sphere(p2, r=s, c=[0.3, 0.3, 0.3]))

    act = Actor(merge(*actors), name="Ruler", br_class="Ruler")
    act.c((0.3, 0.3, 0.3)).alpha(1).lw(2)
    return act


def ruler_from_surface(
    p1, root, unit_scale=1, axis=1, units=None, s=50
) -> Actor:
    """
    Creates a ruler between a point and the brain's surface
    :param p1: list, np.ndarray with coordinates of  point
    :param root: mesh or actor with brain's root
    :param axis: int, index of axis along which distance is computed
    :param unit_scale: float. To scale the units (e.g. show mm instead of µm)
    :param units: str, name of unit (e.g. 'mm')
    :param s: float size of text
    """
    logger.debug(f"Creating a ruler actor between {p1} and brain surface")
    # Get point on brain surface
    p2 = p1.copy()
    p2[axis] = 0  # zero the choosen coordinate

    pts = root.mesh.intersectWithLine(p1, p2)
    surface_point = pts[0]

    return ruler(p1, surface_point, unit_scale=unit_scale, units=units, s=s)
