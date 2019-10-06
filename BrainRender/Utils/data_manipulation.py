def get_coords(obj, mirror=False, mirror_ax='x'):
    """[Get the XYZ coordinates of an object. Can take a dict, Pandas Dataframe or Series]
    
    Arguments:
        obj {[dict, DataFrame, Series]} -- [some variable with fields X Y Z from which the coordinates can be extracted]
    """
    if len(obj) == 0: raise ValueError

    try:
        z,y,x =  obj["z"].values[0], obj["y"].values[0], obj["x"].values[0]
    except:
        if isinstance(obj['z'], list):
            z, y, x = obj["z"][0], obj["y"][0], obj["x"][0]
        else:
            z,y,x = obj["z"], obj["y"], obj["x"]
        
    if not isinstance(z, float): raise ValueError("Could not extract coordinates from: {}".format(obj)) 
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
    flatten = []
    for item in lst:
        if isinstance(item, list):
            flatten.extend(item)
        else:
            flatten.append(item)
    return flatten

def is_any_item_in_list(L1, L2):
    # checks if any item of L1 is also in L2 and returns false otherwise
    inboth = [i for i in L1 if i in L2]
    if inboth:
        return True
    else:
        return False

def get_slice_coord(bounds, n):
    """
        # Given the bounds of an actor, return the point that 
        # corresponds to the n% of the bounds range

        bounds should be a list of two floats
        n should be a float in range 0, 1
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

def mirror_actor_at_point(actor, point, axis='x'):
    if not isinstance(actor, dict):
        coords = actor.coordinates()
        if axis == 'x':
            shifted_coords = [[c[0], c[1], point + (point-c[2])] for c in coords]
        elif axis == 'y':
            shifted_coords = [[c[0], point + (point-c[1]), c[2]] for c in coords]
        elif axis == 'z':
            shifted_coords = [[point + (point-c[0]), c[1], c[2]] for c in coords]
        
        actor.setPoints(shifted_coords)
        actor = actor.mirror(axis='n') # to make sure that the mirrored actor looks correctly
        return actor
    else:
        mirrored_actor = {}
        for n, a in actor.items():
            coords = a.coordinates()
            if axis == 'x':
                shifted_coords = [[c[0], c[1], point + (point-c[2])] for c in coords]
            elif axis == 'y':
                shifted_coords = [[c[0], point + (point-c[1]), c[2]] for c in coords]
            elif axis == 'z':
                shifted_coords = [[point + (point-c[0]), c[1], c[2]] for c in coords]
            
            a.setPoints(shifted_coords)
            a = a.mirror(axis='n') # to make sure that the mirrored actor looks correctly
            mirrored_actor[n] = actor
        return mirrored_actor




