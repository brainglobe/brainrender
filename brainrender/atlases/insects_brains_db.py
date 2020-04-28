

import pandas as pd
import numpy as np
import os
from tqdm import tqdm
from PIL import ImageColor

from vtkplotter import load

from brainrender.atlases.base import Atlas
from brainrender.Utils.webqueries import request
from brainrender.Utils.data_io import load_mesh_from_file

"""
    Class to download and render a number of insect brains from:
    https://insectbraindb.org/app/

    The InsectBrainDB.org is primarily curated by Stanley Heinze

    The insectbraindb.org has a terms of use, which provides guidance on how best to credit data from these repositories. 

    The insectbraindb.org is primarily curated by Dr. Stanley Heinze, and 
    was buily by Kevin Tedore, and has several significant supporters, including the ERC.
"""



class IBDB(Atlas):

    _base_url = "https://insectbraindb.org"
    _url_paths = dict(
        brain_info = "archive/species/most_current_permitted/?species_id=",
        species_info = "api/species/min/",
        data = "https://s3.eu-central-1.amazonaws.com/ibdb-file-storage",
    )
    
    def __init__(self, 
                species = None, sex=None,
                base_dir=None, **kwargs):
        Atlas.__init__(self, base_dir=base_dir, **kwargs)

        # Get a list of available species
        self.species_info = pd.DataFrame(request(f"{self._base_url}/{self._url_paths['species_info']}").json())
        self.species = list(self.species_info.scientific_name.values)

        # Get selected species
        self.sel_species = species
        self.sex = sex
        self.structures = self.get_brain(species=species, sex=sex)

    
    def get_brain_id_from_species_name(self, sel_species):
        if sel_species not in self.species:
            raise ValueError(f"The species {sel_species} is not among the available species {self.species}")
        
        brain_id = self.species_info.loc[self.species_info.scientific_name == sel_species]['id'].values[0]
        return brain_id

    def get_brain(self, species=None, sex=None):
        # Get metadata about the brain from database
        if species is None:
            species = self.sel_species

        if species is None:
            print("No species name passed")
            return None

        self.species = species
        self.sex = sex

        iid = self.get_brain_id_from_species_name(species)

        data = request(f"{self._base_url}/{self._url_paths['brain_info']}{iid}").json()
        if not len(data):
            print("Could not get any data for this brain")
            return None

        # Get reconstructions
        reconstructions = [r['viewer_files'] for r in data['reconstructions']]
        n_elems = [len(rec) for rec in reconstructions]

        if sex is None:
            sex = np.argmax(n_elems)
        
        if not n_elems[sex]:
            raise ValueError(f"No reconstructions found for {sex} {species}")
        else:
            reconstruction = reconstructions[sex]

        # Get data about the brain regions
        structures = dict(
            name = [],
            acronym = [],
            color=[],
            obj_path = [],
            hemisphere = [],
        )

        for d in reconstruction:
            structures['obj_path'].append(d['p_file']['path'])

            hemi = d['structures'][0]['hemisphere']
            if hemi is None:
                hemi = "both"
            structures['hemisphere'].append(hemi.lower())

            if hemi == 'right':
                name = d['structures'][0]['structure']['name'] + "_R"
                acro = d['structures'][0]['structure']['abbreviation'] + "_R"
            elif hemi == 'left':
                name = d['structures'][0]['structure']['name'] + "_L"
                acro = d['structures'][0]['structure']['abbreviation'] + "_L"
            else:
                name = d['structures'][0]['structure']['name'] 
                acro = d['structures'][0]['structure']['abbreviation'] 

            structures['name'].append(name)
            structures['acronym'].append(acro)
            structures['color'].append(d['structures'][0]['structure']['color'])
        self.structures = pd.DataFrame(structures)

        # Prep some vars
        self.region_acronyms = list(self.structures['acronym'])
        self.regions = list(self.structures['name'])

        meshes_fld = os.path.join(self.ibdb_meshes_folder, self.species)
        if not os.path.isdir(meshes_fld):
            print("Creating folder at: {}".format(meshes_fld))
            os.makedirs(meshes_fld)
        self.meshes_folder = meshes_fld

    def download_and_save_mesh(self, acronym, obj_path):
        print(f"Downloading mesh data for {acronym}")
        path = self.structures.loc[self.structures.acronym == acronym].obj_path.values[0]
        url = f"{self._url_paths['data']}/{path}"

        # download and save .obj
        mesh_data = request(url).content.decode("utf-8").split("\n")
        with open(obj_path, 'w') as f:
            for md in mesh_data:
                f.write(f"{md}\n")
            f.close()

        # return the vtk actor
        return load(obj_path)



    # ---------------------------------------------------------------------------- #
    #                          Replace base atlas methods                          #
    # ---------------------------------------------------------------------------- #
    
    def _get_structure_mesh(self, acronym,   **kwargs):
        """
        Fetches the mesh for a brain region from the atlas.

        :param acronym: string, acronym of brain region
        :param **kwargs:

        """
        if self.structures is None: 
            print("No atlas was loaded, use self.get_brain first")
            return None

        if acronym not in self.structures['acronym'] and acronym != 'root':
            raise ValueError(f"Acronym {acronym} not in available regions: {self.structures}")
        if acronym not in self.structures['acronym'] and acronym == 'root':
            return None

        # Get obj file path
        obj_path = os.path.join(self.meshes_folder, "{}.obj".format(acronym))

        # Load
        if self._check_obj_file(structure, obj_path):
            mesh = load_mesh_from_file(obj_path, **kwargs)
            return mesh
        else:
            mesh = self.download_and_save_mesh(acronym, obj_path)
            return None

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
            return ImageColor.getrgb(self.structures.loc[self.structures.acronym == regions].color.values[0])
        else:
            colors = []
            for region in regions:
                if not self._check_valid_region_arg(region):
                    return None
                colors.append(ImageColor.getrgb(self.structures.loc[self.structures.acronym == region].color.values[0]))
            return colors






