import sys
sys.path.append('./')

import os
import pandas as pd
from vtkplotter import load

from brainrender import DEFAULT_STRUCTURE_COLOR


def get_rat_regions_metadata(metadata_fld):
    """

    :param metadata_fld: 

    """
    return pd.read_pickle(os.path.join(metadata_fld, "rat_structures.pkl"))

def get_rat_mesh_from_region(region, paths, use_original_color=False, **kwargs):
    """

    :param region: 
    :param paths: 
    :param use_original_color:  (Default value = False)
    :param **kwargs: 

    """
    if not isinstance(region, (tuple, list)):
        region = [region]
        check = False
    else: check = True

    metadata = get_rat_regions_metadata(paths.metadata)

    meshes = []
    for reg in region:
        if isinstance(reg, int):
            entry = metadata.loc[metadata.Id == reg]
        elif isinstance(reg, str):
            entry = metadata.loc[metadata['Name'] == reg]
        else:
            raise ValueError("Unrecognized value for region while trying to get mesh for rat: {}".format(reg))
            
        try:
            meshname = os.path.join(paths.rat_meshes, "label_{}.stl".format(entry.Id.values[0]))

            if not os.path.isfile(meshname):
                raise FileExistsError(meshname)

            if use_original_color:
                c = entry["rgb"].values[0]
                if isinstance(c, str):
                    c = c.replace("[", "")
                    c = c.replace("]", "")
                    cols = c.split(",")
                    color = [int(c) for c in cols]
                else:
                    color = c
            else:
                if "color" in list(kwargs.keys()):
                    color = kwargs.pop("color", DEFAULT_STRUCTURE_COLOR)
                elif "c" in list(kwargs.keys()):
                    color = kwargs.pop("c", DEFAULT_STRUCTURE_COLOR)

            if "color" in list(kwargs.keys()): del kwargs["color"]
            elif "c" in list(kwargs.keys()): del kwargs["c"]

            mesh = load(meshname, c=color, **kwargs) 
            mesh = mesh.smoothLaplacian().subdivide(2)
            meshes.append(mesh)
        except:
            print("Could not load rat region: {}".format(entry["Name"].values[0]))
            return None
    
    if not check:
        return meshes[0]
    else:
        return meshes

if __name__ == "__main__":
    pass
    #fix_data() ## UNDEFINED!!??
