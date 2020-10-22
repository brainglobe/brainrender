import numpy as np

from vedo import merge
from vedo.shapes import Line, Sphere, Text
from vedo.utils import precision, mag


def ruler(p1, p2, unit_scale=1, units=None, s=50):
    actors = []

    # Make two line segments
    midpoint = np.array([(x + y) / 2 for x, y in zip(p1, p2)])
    gap1 = ((midpoint - p1) * 0.8) + p1
    gap2 = ((midpoint - p2) * 0.8) + p2

    actors.append(Line(p1, gap1, lw=200))
    actors.append(Line(gap2, p2, lw=200))

    # Add label
    if units is None:
        units = ""
    dist = mag(p2 - p1) * unit_scale
    label = precision(dist, 3) + " " + units
    lbl = Text(label, pos=midpoint, s=s + 100, justify="center")
    lbl.SetOrientation([0, 0, 180])
    actors.append(lbl)

    # Add spheres add end
    actors.append(Sphere(p1, r=s, c=[0.3, 0.3, 0.3]))
    actors.append(Sphere(p2, r=s, c=[0.3, 0.3, 0.3]))

    acts = merge(*actors).c((0.3, 0.3, 0.3)).alpha(1).lw(2)
    acts.name = "Ruler"
    acts.bg_class = "Ruler"
    return acts
