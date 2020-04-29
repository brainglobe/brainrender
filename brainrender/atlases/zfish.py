

import pandas as pd
import numpy as np
import os
from tqdm import tqdm
from PIL import ImageColor

from vtkplotter import load, delaunay3D, Mesh
from vtkplotter.vtkio import save
from vtkplotter.utils import geometry
from vtkplotter.analysis import recoSurface

from brainrender.atlases.base import Atlas
from brainrender.Utils.webqueries import request
from brainrender.Utils.data_io import load_mesh_from_file

"""
    This atlas supports the download and rendering of brain regions and 
    neurons reconstructions from https://www.neuro.mpg.de/baier/connectome
    and https://fishatlas.neuro.mpg.de/
"""



class ZFISH(Atlas):

    atlas_name = "ZebraFish"
    mesh_format = 'obj'

    _base_url = "https://fishatlas.neuro.mpg.de"
    _url_paths = dict(
        brain = "neurons/get_brain",
        brain_regions = "neurons/get_brain_regions",
    )
    
    def __init__(self, 
                base_dir=None, **kwargs):
        Atlas.__init__(self, base_dir=base_dir, **kwargs)

        # Get brain regions metadata
        self.structures = self.get_brain_regions_metadata()
        self.region_acronyms = list(self.structures['name'])
        self.regions = list(self.structures['name'])

        # Output folder
        self.meshes_folder = self.zfish_meshes_folder


    def get_brain_regions_metadata(self):
        complete_url = f"{self._base_url}/{self._url_paths['brain_regions']}"
        regions = request(complete_url).json()
        metadata = dict(
            name = [],
            parent = [],
            children = [],
            color = [],
            file = [],
        )

        for region in regions['brain_regions']:
            metadata['name'].append(region['name'])
            metadata['parent'].append(None)
            metadata['children'].append([c['name'] for c in region['sub_regions']])
            metadata['color'].append(region['color'])
            metadata['file'].append(region['files']['file_3D'])

            for subreg in region['sub_regions']:
                metadata['name'].append(subreg['name'])
                metadata['parent'].append(region['name'])
                metadata['children'].append([c['name'] for c in subreg['sub_regions']])
                metadata['color'].append(subreg['color'])
                metadata['file'].append(subreg['files']['file_3D'])

                for subsubreg in subreg['sub_regions']:
                    metadata['name'].append(subsubreg['name'])
                    metadata['parent'].append([region['name'], subreg['name']])
                    metadata['children'].append(None)
                    metadata['color'].append(subsubreg['color'])
                    metadata['file'].append(subsubreg['files']['file_3D'])

        # Get root
        metadata['name'].append('root')
        metadata['parent'].append(None)
        metadata['children'].append([c['name'] for c in regions['brain_regions']])
        metadata['color'].append('#d3d3d3')
        metadata['file'].append(None)
        return pd.DataFrame(metadata)
        

    def download_and_save_mesh(self, region, obj_path):
        print(f"Downloading mesh data for {region}")
        path = self.structures.loc[self.structures.name == region].file.values[0]

        if region != 'root':
            if not path or path is None:
                print(f"Could not find mesh for {region}")
                return None

        if region == "root":
            complete_url = f"{self._base_url}/{self._url_paths['brain']}"
            req = request(complete_url).json()

            fp = req['brain']['outline']['file'].replace("\\", "/")
            url = f"{self._base_url}/{fp}"
        else:
            url = f"{self._base_url}/{path}".replace("\\", "/")
            
        req = request(url)

        # download render and save .obj
        data = [float(v) for v in req.content.decode("-utf8").split("\n") if v]
        data = np.array(data).reshape((-1, 3)) # x y z coordinates of each vertex
        data = pd.DataFrame(dict(
            x = data[:, 0],
            y = data[:, 1],
            z = data[:, 2]
        ))
        # data = data.drop_duplicates()

        mesh = recoSurface(data.values, dims=data.max().values.astype(np.int32),
                            radius=7.5) #.decimate(0.5) # 8.99
        # mesh.smoothMLS2D(f=0.8)

        save(mesh, obj_path)
        
        # return the vtk actor
        return load(obj_path)



    # ---------------------------------------------------------------------------- #
    #                          Replace base atlas methods                          #
    # ---------------------------------------------------------------------------- #
    
    def _get_structure_mesh(self, region,   **kwargs):
        """
        Fetches the mesh for a brain region from the atlas.

        :param region: string, name of brain region
        :param **kwargs:

        """
        if self.structures is None: 
            print("No atlas was loaded, use self.get_brain first")
            return None

        if region not in list(self.structures['name']):
            print(f"Acronym {region} not in available regions: {self.structures}")
            return None

        # Get obj file path
        obj_path = os.path.join(self.meshes_folder, "{}.vtk".format(region))

        # Load
        if self._check_obj_file(region, obj_path):
            mesh = load_mesh_from_file(obj_path, **kwargs)
            return mesh
        else:
            mesh = self.download_and_save_mesh(region, obj_path)
            return mesh

    def _check_valid_region_arg(self, region):
        """
        Check that the string passed is a valid brain region name.
        """
        if self.structures is None:
            return False
        else:
            if region not in self.region_acronyms:
                return False
        return True

    def _check_obj_file(self, region, obj_file):
        """
        If the .obj file for a brain region hasn't been downloaded already, this function downloads it and saves it.

        :param region: string, acronym of brain region
        :param obj_file: path to .obj file to save downloaded data.

        """
        # checks if the obj file has been downloaded already, if not it takes care of downloading it
        if not os.path.isfile(obj_file):
            self.download_and_save_mesh(region, obj_file)
        return True

    def get_region_color(self, regions):
        """
        Gets the RGB color of a brain region from the Allen Brain Atlas.

        :param regions:  list of regions acronyms.

        """
        if not isinstance(regions, list):
            if not self._check_valid_region_arg(regions):
                return None
            return ImageColor.getrgb(self.structures.loc[self.structures.name == regions].color.values[0])
        else:
            colors = []
            for region in regions:
                if not self._check_valid_region_arg(region):
                    return None
                colors.append(ImageColor.getrgb(self.structures.loc[self.structures.name == region].color.values[0]))
            return colors






