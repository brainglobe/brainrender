import sys
sys.path.append('./')

import os
import pandas as pd
from vtkplotter import *

from BrainRender.colors import *
from BrainRender.variables import *

def fix_data():
    # data = {"Id":[], "Name":[], "rgb":[]}
    # for i, row in pd.read_csv("rat_structures.csv").iterrows():
    #     s = row.values[0].replace("[", "")
    #     s = s.replace("]", "")
    #     s = s.replace('"', "")
    #     vals = s.split(",")

    #     try: 
    #         int(vals[3])
    #         check=True
    #     except:
    #         check=False

    #     if check:
    #         data["Id"].append(int(vals[1]))
    #         data["Name"].append(vals[2])
    #         data["rgb"].append([int(vals[3]), int(vals[4]), int(vals[5])])
    #     else:
    #         data["Id"].append(int(vals[1]))
    #         data["Name"].append(vals[2]+", "+vals[3])
    #         data["rgb"].append([int(vals[4]), int(vals[5]), int(vals[6])])

    # data = pd.DataFrame.from_dict(data)

    data = pd.read_csv("rat_structures.csv")
    data = data.drop("Unnamed: 0", axis=1)
    data.to_csv("rat_structures.csv")
    data.to_pickle("rat_structures.pkl")

def get_rat_regions_metadata():
    return pd.read_pickle("rat_structures.pkl")

def get_rat_mesh_from_region(region, use_original_color=False, **kwargs):
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

            mesh = load(meshname, c=color, **kwargs) # 
            mesh = mesh.smoothLaplacian().subdivide(1)
            meshes.append(mesh)
        except:
            print("Could not load rat region: {}".format(entry["Name"].values[0]))
            return None
    
    if not check:
        return meshes[0]
    else:
        return meshes

if __name__ == "__main__":
    fix_data()
