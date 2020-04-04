def get_coords(obj, mirror=False, mirror_ax='x'):
    """
    Takes coordinates in various format and turns them into what's expected from VTK plotter for rendering. 
    Can take a dict, Pandas Dataframe or Series

    :param obj: dict, pandas.DataFrame or pandas.Series
    :param mirror:  if True, the coordinates are mirrored around mirror_ax (Default value = False)
    :param mirror_ax: ax to be used for mirroring ['x', 'y', 'z'] (Default value = 'x')

    """
    if len(obj) == 0: raise ValueError

    try:
        z,y,x =  obj["z"].values[0], obj["y"].values[0], obj["x"].values[0]
    except:
        if isinstance(obj, list) and len(obj) == 3:
            z, y, x = obj[0], obj[1], obj[2]
        elif isinstance(obj, list) and len(obj) != 3:
            raise ValueError("Could not extract coordinates from: {}".format(obj)) 
        elif isinstance(obj['z'], list):
            z, y, x = obj["z"][0], obj["y"][0], obj["x"][0]
        else:
            z,y,x = obj["z"], obj["y"], obj["x"]
        
    if not isinstance(z, (float, int)): raise ValueError("Could not extract coordinates from: {}".format(obj)) 
    else: 
        if mirror is None: mirror = False
        if mirror and mirror_ax == 'x':
            x = mirror + (mirror-x)
        if mirror and mirror_ax == 'y':
            y = mirror + (mirror-y)
        if mirror and mirror_ax == 'z':
            z = mirror + (mirror-z)
        return z,y,x

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
    if not isinstance(bounds,(list, tuple)) or not isinstance(bounds[0],float) or not isinstance(bounds[1],float):
        raise ValueError("bounds should be a list or tuple of floats: {}".format(bounds))
    if not isinstance(n, (int, float)):
        raise ValueError("n should be a float")
    if n < 0 or n > 1:
        raise ValueError("n should be in range [0, 1]")


    b0, b1 = bounds
    delta = b1 - b0

    return b0 + delta*n






