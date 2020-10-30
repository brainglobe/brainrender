from vedo import Text, Sphere
import numpy as np

from ._utils import listify


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
            color = actor.c()

        # Get mesh's highest point
        points = actor.points().copy()
        point = points[np.argmin(points[:, 1]), :]
        point += np.array(offset) + default_offset

        try:
            if atlas.hemisphere_from_coords(point, as_string=True) == "left":
                point = atlas.mirror_point_across_hemispheres(point)
        except IndexError:
            pass

        # Create label
        txt = Text(label, point, s=size, c=color)
        txt._kwargs = dict(
            size=size,
            color=color,
            radius=radius,
            xoffset=xoffset,
            yoffset=yoffset,
            zoffset=zoffset,
        )

        new_actors.append(txt)

        # Mark a point on Mesh that corresponds to the label location
        if radius is not None:
            pt = actor.closestPoint(point)
            sphere = Sphere(pt, r=radius, c=color)
            sphere.ancor = pt
            new_actors.append(sphere)

    return new_actors
