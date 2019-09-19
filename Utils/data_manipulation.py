def get_coords(obj):
    """[Get the XYZ coordinates of an object. Can take a dict, Pandas Dataframe or Series]
    
    Arguments:
        obj {[dict, DataFrame, Series]} -- [some variable with fields X Y Z from which the coordinates can be extracted]
    """
    if len(obj) == 0: raise ValueError

    try:
        z,y,x =  obj["z"].values[0], obj["y"].values[0], obj["x"].values[0]
    except:
        z,y,x = obj["z"], obj["y"], obj["x"]

    if not isinstance(z, float): raise ValueError("Could not extract coordinates from: {}".format(obj)) 
    else: 
        return z,y,x