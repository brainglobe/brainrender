import numpy as np

""" 
    Collection of functions to edit actors looks and other features.
"""


def get_actor_bounds(actor):
    """
        Gets the AP-DV-ML bounds of an actor
    """
    bounds = actor.bounds()
    return [
        [bounds[0], bounds[1]],
        [bounds[2], bounds[3]],
        [bounds[4], bounds[5]],
    ]


def get_actor_midpoint(actor):
    """ 
        Get's the coordinates of the midpoint of an
        actor (vedo.Mesh)
    """
    return [np.mean(bounds) for bounds in get_actor_bounds(actor)]


# TODO mirror around point would mean
def mirror_actor_at_point(actor, point, axis="x"):
    """
    Mirror an actor around a point

    :param actor: 
    :param point: 
    :param axis:  (Default value = 'x')

    """
    if not isinstance(actor, dict):
        coords = actor.points()
        if axis == "x":
            shifted_coords = [
                [c[0], c[1], point + (point - c[2])] for c in coords
            ]
        elif axis == "y":
            shifted_coords = [
                [c[0], point + (point - c[1]), c[2]] for c in coords
            ]
        elif axis == "z":
            shifted_coords = [
                [point + (point - c[0]), c[1], c[2]] for c in coords
            ]

        actor.points(shifted_coords)
        actor = actor.mirror(
            axis="n"
        )  # to make sure that the mirrored actor looks correctly
        return actor
    else:
        mirrored_actor = {}
        for n, a in actor.items():
            coords = a.points()
            if axis == "x":
                shifted_coords = [
                    [c[0], c[1], point + (point - c[2])] for c in coords
                ]
            elif axis == "y":
                shifted_coords = [
                    [c[0], point + (point - c[1]), c[2]] for c in coords
                ]
            elif axis == "z":
                shifted_coords = [
                    [point + (point - c[0]), c[1], c[2]] for c in coords
                ]

            a.points(shifted_coords)
            a = a.mirror(
                axis="n"
            )  # to make sure that the mirrored actor looks correctly
            mirrored_actor[n] = actor
        return mirrored_actor


def set_line(actor, lw=None, c=None):
    """
    set an actor's look to specify the line width and color

    :param actor: 
    :param lw:  (Default value = None)
    :param c:  (Default value = None)

    """
    if lw is not None:
        actor.lw(lineWidth=lw)
    if c is not None:
        actor.lc(lineColor=c)


def edit_actor(
    actor,
    wireframe=False,
    solid=False,
    color=False,
    line=False,
    line_kwargs={},
    upsample=False,
    downsample=False,
    smooth=False,
):
    """
    Apply a set of functions to edit an actor's look. 

    :param actor: 
    :param wireframe: if true, change look to wireframe (Default value = False)
    :param solid: if true change look to soi=lid (Default value = False)
    :param color: specify new color (Default value = False)
    :param line: if true, edit the line's look (Default value = False)
    :param line_kwargs: specify width and color of line (Default value = {})
    :param upsample: if true, increase resolution (Default value = False)
    :param downsample: if true, decrease resolution (Default value = False)
    :param smooth: if true, smoothen actor (Default value = False)

    """

    if wireframe:
        actor.wireframe(value=True)
    if solid:
        actor.wireframe(value=False)
    if color:
        actor.color(c=color)
    if line:
        set_line(actor, **line_kwargs)
    if upsample:
        actor.subdivide(N=1)
    if downsample:
        actor.decimate(fraction=0.5)
    if smooth:
        actor.smoothLaplacian(niter=15)
