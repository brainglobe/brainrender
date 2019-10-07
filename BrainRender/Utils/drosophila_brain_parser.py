import sys
sys.path.append('./')

import os
import pandas as pd
from vtkplotter import *

from BrainRender.colors import *
from BrainRender.variables import *


def get_drosophila_regions_metadata():
    return pd.read_pickle("Metadata/drosophila_structures.pkl")


def get_drosophila_mesh_from_region(region, **kwargs):
    if not isinstance(region, (tuple, list)):
        region = [region]
        check = False
    else: check = True

    metadata = get_drosophila_regions_metadata()

    if "color" in list(kwargs.keys()):
        color = kwargs.pop("color", DEFAULT_STRUCTURE_COLOR)
    elif "c" in list(kwargs.keys()):
        color = kwargs.pop("c", DEFAULT_STRUCTURE_COLOR)

    if "color" in list(kwargs.keys()): del kwargs["color"]
    elif "c" in list(kwargs.keys()): del kwargs["c"]


    meshes = []
    for reg in region:
        if reg.lower() == "root":
            meshname = drosophila_root
            mesh = load(meshname, c=color, **kwargs) 
            mesh = mesh.smoothLaplacian().subdivide(2)
            meshes.append(mesh)
        else:
            if isinstance(reg, int):
                entry = metadata.loc[metadata.Id == reg]
            elif isinstance(reg, str):
                entry = metadata.loc[metadata['acronym'] == reg]
            else:
                raise ValueError("Unrecognized value for region while trying to get mesh for rat: {}".format(reg))
                
            try:
                eid = entry.Id.values[0]
                if len(eid) == 1:
                    meshname = "Meshes/drosophila_meshes/domains/AdultBrainDomain000{}.obj".format(eid)
                if len(eid) == 2:
                    meshname = "Meshes/drosophila_meshes/domains/AdultBrainDomain00{}.obj".format(eid)
                if len(eid) == 3:
                    meshname = "Meshes/drosophila_meshes/domains/AdultBrainDomain0{}.obj".format(eid)

                if not os.path.isfile(meshname):
                    raise FileExistsError(meshname)

                mesh = load(meshname, c=color, **kwargs) 
                mesh = mesh.smoothLaplacian().subdivide(2)
                meshes.append(mesh)
            except:
                print("Could not load rat region: {}".format(entry["acronym"].values[0]))
                return None
    
    if not check:
        return meshes[0]
    else:
        return meshes

def fix_data():
    with open("Metadata/drosophila.txt", "r") as f:
        content = f.readlines()

    data = {"acronym":[], "name":[], "Id":[]}
    for i,line in enumerate(content):
        if i == 0: continue
        line = line.replace("\n", '')
        line = line.split("\t")

        data['acronym'].append(line[0])
        data['name'].append(line[1])
        data['Id'].append(line[2])

    data = pd.DataFrame(data)
    data.to_pickle("Metadata/drosophila_structures.pkl")

def remove_extra_meshes():
    fld = "/Users/federicoclaudi/Documents/Github/BrainRender/Meshes/drosophila_meshes/domains"
    for f in os.listdir(fld):
        print(f)
        if "_" in f or ".txt" in f:
            os.remove(os.path.join(fld, f))


if __name__ == "__main__":
    remove_extra_meshes()