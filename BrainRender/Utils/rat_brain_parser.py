import sys
sys.path.append('./')

import os
import pandas as pd

from vtkplotter import *

def fix_data():
    data = {"Id":[], "Name":[], "rgb":[]}
    for i, row in pd.read_csv("rat_structures.csv").iterrows():
        s = row.values[0].replace("[", "")
        s = s.replace("]", "")
        s = s.replace('"', "")
        vals = s.split(",")

        try: 
            int(vals[3])
            check=True
        except:
            check=False

        if check:
            data["Id"].append(int(vals[1]))
            data["Name"].append(vals[2])
            data["rgb"].append([int(vals[3]), int(vals[4]), int(vals[5])])
        else:
            data["Id"].append(int(vals[1]))
            data["Name"].append(vals[2]+", "+vals[3])
            data["rgb"].append([int(vals[4]), int(vals[5]), int(vals[6])])

    data = pd.DataFrame.from_dict(data)
    data.to_csv("rat_structures.csv")
    data.to_pickle("rat_structures.pkl")

def get_rat_regions_metadata():
    return pd.read_pickle("rat_structures.pkl")

def get_rat_mesh_from_region(region, **kwargs):
    if not isinstance(region, (tuple, list)):
        region = [region]
        check = False
    else: check = True

    metadata = get_rat_regions_metadata()

    meshes = []
    for reg in region:
        if isinstance(reg, int):
            entry = metadata.loc[metadata.Id == reg]
        elif isinstance(reg, str):
            entry = metadata.loc[metadata['Name'] == reg]
        else:
            raise ValueError("Unrecognized value for region while trying to get mesh for rat: {}".format(reg))
            
        try:
            meshname = "Meshes/rat_meshes/label_{}.stl".format(entry.Id.values[0])

            if not os.path.isfile(meshname):
                raise FileExistsError(meshname)

            meshes.append(load(meshname, **kwargs))
        except:
            raise ValueError("Could not load rat region:\n {}".format(entry))
    
    if not check:
        return meshes[0]
    else:
        return meshes


