# ---------------------------------------------------------------------------- #
#                                PYTHON OBJECTS                                #
# ---------------------------------------------------------------------------- #


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


# ---------------------------------------------------------------------------- #
#                             BRAINRENDER SPECIFIC                             #
# ---------------------------------------------------------------------------- #


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


def make_optic_canula_cylinder(
    atlas,
    root,
    target_region=None,
    pos=None,
    offsets=(0, 0, -500),
    hemisphere="right",
    color="powderblue",
    radius=350,
    alpha=0.5,
    **kwargs,
):

    """
        Creates a cylindrical vedo actor to scene to render optic cannulas. By default
        this is a semi-transparent blue cylinder centered on the center of mass of
        a specified target region and oriented vertically.

        :param target_region: str, acronym of target region to extract coordinates
            of implanted fiber. By defualt the fiber will be centered on the center
            of mass of the target region but the offset arguments can be used to
            fine tune the position. Alternative pass a 'pos' argument with AP-DV-ML coords.
        :param pos: list or tuple or np.array with X,Y,Z coordinates. Must have length = 3.
        :param x_offset, y_offset, z_offset: int, used to fine tune the coordinates of 
            the implanted cannula.
        :param **kwargs: used to specify which hemisphere the cannula is and parameters
            of the rendered cylinder: color, alpha, rotation axis...
    """

    # Get coordinates of brain-side face of optic cannula
    if target_region is not None:
        pos = atlas.get_region_CenterOfMass(
            target_region, unilateral=True, hemisphere=hemisphere
        )
    elif pos is None:
        print(
            "No 'pos' or 'target_region' arguments were \
                        passed to 'add_optic_cannula', nothing to render"
        )
        return

    # Offset position
    for i, offset in enumerate(offsets):
        pos[i] += offset

    # Get coordinates of upper face
    bounds = root.bounds()
    top = pos.copy()
    top[1] = bounds[2] - 500

    # Create actor
    return dict(pos=[top, pos], c=color, r=radius, alpha=alpha, **kwargs)


def get_cells_in_region(atlas, cells, region):
    """
        Selects the cells that are in a list of user provided 
        brain regions from a dataframe of cell locations

        :param cells: pd.DataFrame of cells x,y,z coordinates
    """
    if isinstance(region, list):
        region_list = []
        for reg in region:
            region_list.extend(list(atlas.get_structure_descendants(reg)))
    else:
        region_list = list(atlas.get_structure_descendants(region))
    return cells[cells.region.isin(region_list)]
