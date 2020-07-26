import numpy as np
import inspect
from vedo import Mesh, Text, Sphere
import random

from brainrender.atlases.atlas import Atlas
import brainrender
from brainrender.Utils.camera import check_camera_param
from brainrender.colors import get_random_colors


def get_scene_atlas(atlas, base_dir, atlas_kwargs={}, **kwargs):
    """
        Return an instance of an Atlas class. 

    """
    if atlas is None:
        atlas = brainrender.DEFAULT_ATLAS

    if isinstance(atlas, str):
        return Atlas(atlas, base_dir=base_dir, **atlas_kwargs, **kwargs,)
    elif inspect.isclass(atlas):
        return atlas(**atlas_kwargs)
    else:
        raise ValueError(
            "The `atlas` argument should be None, a string with atlas name or a class"
        )


def get_scene_camera(camera, atlas):
    """
        Gets a working camera. 
        In order these alternatives are used:
            - user given camera
            - atlas specific camera
            - default camera
    """
    if camera is None:
        if atlas.default_camera is not None:
            return check_camera_param(atlas.default_camera)
        else:
            return brainrender.CAMERA
    else:
        return check_camera_param(camera)


def get_scene_plotter_settings(jupyter):
    """
        Gets settings for vedo Plotter
    """

    if brainrender.WHOLE_SCREEN and not jupyter:
        sz = "full"
    elif brainrender.WHOLE_SCREEN and jupyter:
        print(
            "Setting window size to 'auto' as whole screen is not available in jupyter"
        )
        sz = "auto"
    else:
        sz = "auto"

    if brainrender.SHOW_AXES:
        axes = 1
    else:
        axes = 0

    return dict(
        size=sz, axes=axes, pos=brainrender.WINDOW_POS, title="brainrender"
    )


def get_cells_colors_from_metadata(color_by_metadata, coords_df, color):
    """
        Get color of each cell given some metadata entry

        :param color_by_metadata: str, column name with metadata info
        :param coords_df: dataframe with cell coordinates and metadata
    """

    if color_by_metadata not in coords_df.columns:
        raise ValueError(
            'Color_by_metadata argument should be the name of one of the columns of "coords"'
        )

    # Get a map from metadata values to colors
    vals = list(coords_df[color_by_metadata].values)
    if len(vals) == 0:
        raise ValueError(
            f"Cant color by {color_by_metadata} as no values were found"
        )
    if not isinstance(
        color, dict
    ):  # The user didn't pass a lookup, generate random
        base_cols = get_random_colors(n_colors=len(set(vals)))
        cols_lookup = {v: c for v, c in zip(set(vals), base_cols)}
    else:
        try:
            for val in list(set(vals)):
                color[val]
        except KeyError:
            raise ValueError(
                'While using "color_by_metadata" with a dictionary of colors passed'
                + ' to "color", not every metadata value was assigned a color in the dictionary'
                + " please make sure that the color dictionary is complete"
            )
        else:
            cols_lookup = color

    # Use the map to get a color for each cell
    color = [cols_lookup[v] for v in vals]

    return color


def make_actor_label(
    atlas,
    actors,
    labels,
    size=300,
    color=None,
    radius=100,
    xoffset=0,
    yoffset=0,
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
    # Check args
    if not isinstance(actors, (tuple, list)):
        actors = [actors]
    if not isinstance(labels, (tuple, list)):
        labels = [labels]

    if atlas.atlas_name == "ABA":
        offset = [-yoffset, -zoffset, xoffset]
        default_offset = np.array([0, -200, 100])
    else:
        offset = [xoffset, yoffset, zoffset]
        default_offset = np.array([100, 0, -200])

    new_actors = []
    for n, (actor, label) in enumerate(zip(actors, labels)):
        if not isinstance(actor, Mesh):
            raise ValueError(
                f"Mesh must be an instance of Mesh, not {type(actor)}"
            )
        if not isinstance(label, str):
            raise ValueError(f"Label must be a string, not {type(label)}")

        # Get label color
        if color is None:
            color = actor.c()
        elif isinstance(color, (list, tuple)):
            color = color[n]

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
        new_actors.append(txt)

        # Mark a point on Mesh that corresponds to the label location
        if radius is not None:
            pt = actor.closestPoint(point)
            new_actors.append(Sphere(pt, r=radius, c=color))

    return new_actors


def get_n_random_points_in_region(atlas, region, N, hemisphere=None):
    """
    Gets N random points inside (or on the surface) of the mesh defining a brain region.

    :param region: str, acronym of the brain region.
    :param N: int, number of points to return.
    """
    if isinstance(region, Mesh):
        region_mesh = region
    else:
        if hemisphere is None:
            region_mesh = atlas._get_structure_mesh(region)
        else:
            region_mesh = atlas.get_region_unilateral(
                region, hemisphere=hemisphere
            )
        if region_mesh is None:
            return None

    region_bounds = region_mesh.bounds()

    X = np.random.randint(region_bounds[0], region_bounds[1], size=10000)
    Y = np.random.randint(region_bounds[2], region_bounds[3], size=10000)
    Z = np.random.randint(region_bounds[4], region_bounds[5], size=10000)
    pts = [[x, y, z] for x, y, z in zip(X, Y, Z)]

    try:
        ipts = region_mesh.insidePoints(pts).points()
    except:
        ipts = region_mesh.insidePoints(
            pts
        )  # to deal with older instances of vedo
    return random.choices(ipts, k=N)
