import sys
sys.path.append('./')

import os
import pandas as pd
from vtkplotter import load

from brainrender import DEFAULT_STRUCTURE_COLOR


def get_drosophila_regions_metadata(metadata_fld):
    """

    :param metadata_fld: 

    """
    return pd.read_pickle(os.path.join(metadata_fld,"drosophila_structures.pkl"))


def get_drosophila_mesh_from_region(region, paths,  **kwargs):
    """

    :param region: 
    :param paths: 
    :param **kwargs: 

    """
    if not isinstance(region, (tuple, list)):
        region = [region]
        check = False
    else: check = True

    metadata = get_drosophila_regions_metadata(paths.metadata)

    if "color" in list(kwargs.keys()):
        color = kwargs.pop("color", DEFAULT_STRUCTURE_COLOR)
    elif "c" in list(kwargs.keys()):
        color = kwargs.pop("c", DEFAULT_STRUCTURE_COLOR)

    if "color" in list(kwargs.keys()): del kwargs["color"]
    elif "c" in list(kwargs.keys()): del kwargs["c"]


    meshes = []
    for reg in region:
        if reg.lower() == "root":
            meshname = drosophila_root  ## UNDEFINED!!??
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
                    meshname = os.path.join(paths.drosophila_meshes, "domains/AdultBrainDomain000{}.obj".format(eid))
                if len(eid) == 2:
                    meshname = os.path.join(paths.drosophila_meshes, "domains/AdultBrainDomain00{}.obj".format(eid))
                if len(eid) == 3:
                    meshname = os.path.join(paths.drosophila_meshes, "domains/AdultBrainDomain0{}.obj".format(eid))

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

