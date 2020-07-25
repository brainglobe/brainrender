import numpy as np

from vedo import Cylinder
from brainrender.Utils.data_io import get_probe_points_from_sharptrack


def return_list_smart(lst):
    """
        If the list has length > returns the list
        if it has length == 1 it returns the element
        if it has length == 0 it returns None
    """
    if len(lst) > 1:
        return lst
    elif len(lst) == 1:
        return lst[0]
    else:
        return None


def return_dict_smart(dct):
    keys = list(dct.keys())
    if len(keys) == 1:
        return dct[keys[0]]
    elif len(keys) == 0:
        return None
    else:
        return dct


# TODO this function aim at handling too many scenarios, very confusing to read
def get_coords(obj, mirror=False, mirror_ax="x"):
    """
    Takes coordinates in various format and turns them into what's expected from VTK plotter for rendering. 
    Can take a dict, Pandas Dataframe or Series

    :param obj: dict, pandas.DataFrame or pandas.Series
    :param mirror:  if True, the coordinates are mirrored around mirror_ax (Default value = False)
    :param mirror_ax: ax to be used for mirroring ['x', 'y', 'z'] (Default value = 'x')

    """
    if len(obj) == 0:
        raise ValueError

    try:
        z, y, x = obj["z"].values[0], obj["y"].values[0], obj["x"].values[0]
    except:
        if isinstance(obj, list) and len(obj) == 3:
            z, y, x = obj[0], obj[1], obj[2]
        elif isinstance(obj, list) and len(obj) != 3:
            raise ValueError(
                "Could not extract coordinates from: {}".format(obj)
            )
        elif isinstance(obj["z"], list):
            z, y, x = obj["z"][0], obj["y"][0], obj["x"][0]
        else:
            z, y, x = obj["z"], obj["y"], obj["x"]

    if not isinstance(z, (float, int)):
        raise ValueError("Could not extract coordinates from: {}".format(obj))
    else:
        if mirror is None:
            mirror = False
        if mirror and mirror_ax == "x":
            x = mirror + (mirror - x)
        if mirror and mirror_ax == "y":
            y = mirror + (mirror - y)
        if mirror and mirror_ax == "z":
            z = mirror + (mirror - z)
        return z, y, x


def flatten_list(lst):
    """
    Flattens a list of lists
    
    :param lst: list

    """
    flatten = []
    for item in lst:
        if isinstance(item, list):
            flatten.extend(item)
        else:
            flatten.append(item)
    return flatten


def is_any_item_in_list(L1, L2):
    """
    Checks if an item in a list is in another  list

    :param L1: 
    :param L2: 

    """
    # checks if any item of L1 is also in L2 and returns false otherwise
    inboth = [i for i in L1 if i in L2]
    if inboth:
        return True
    else:
        return False


def get_slice_coord(bounds, n):
    """
    Given the bounds of an actor, return the point that
    corresponds to the n% of the bounds range
    

    :param bounds: should be a list of two floats
    :param n: n should be a float in range 0, 1

    """
    if (
        not isinstance(bounds, (list, tuple))
        or not isinstance(bounds[0], float)
        or not isinstance(bounds[1], float)
    ):
        raise ValueError(
            "bounds should be a list or tuple of floats: {}".format(bounds)
        )
    if not isinstance(n, (int, float)):
        raise ValueError("n should be a float")
    if n < 0 or n > 1:
        raise ValueError("n should be in range [0, 1]")

    b0, b1 = bounds
    delta = b1 - b0

    return b0 + delta * n


def parse_sharptrack(
    atlas,
    probe_points_file,
    name,
    color_by_region=True,
    color="salmon",
    radius=30,
    probe_color="blackboard",
    probe_radius=15,
    probe_alpha=1,
):
    """
        Visualises the position of an implanted probe in the brain. 
        Uses the location of points along the probe extracted with SharpTrack
        [https://github.com/cortex-lab/allenCCF].
        It renders the position of points along the probe and a line fit through them.
        Code contributed by @tbslv on github. 
    """

    # Points params
    params = dict(color_by_region=True, color="salmon", radius=30, res=12,)

    # Get the position of probe points and render
    probe_points_df = get_probe_points_from_sharptrack(probe_points_file)

    # Fit a line through the points [adapted from SharpTrack by @tbslv]
    r0 = np.mean(probe_points_df.values, axis=0)
    xyz = probe_points_df.values - r0
    U, S, V = np.linalg.svd(xyz)
    direction = V.T[:, 0]

    # Find intersection with brain surface
    root_mesh = atlas._get_structure_mesh("root")
    p0 = direction * np.array([-1]) + r0
    p1 = (
        direction * np.array([-15000]) + r0
    )  # end point way outside of brain, on probe trajectory though
    pts = root_mesh.intersectWithLine(p0, p1)

    # Define top/bottom coordinates to render as a cylinder
    top_coord = pts[0]
    length = np.sqrt(np.sum((probe_points_df.values[-1] - top_coord) ** 2))
    bottom_coord = top_coord + direction * length

    # Render probe as a cylinder
    probe = Cylinder(
        [top_coord, bottom_coord],
        r=probe_radius,
        alpha=probe_alpha,
        c=probe_color,
    )
    probe.name = name

    return probe_points_df, params, probe, color
