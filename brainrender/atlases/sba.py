"""
    Developing code to visualise atlases from:
        https://scalablebrainatlas.incf.org/index.php
"""
import os
import numpy as np
import pandas as pd
from PIL import ImageColor
from skimage import measure


from vtkplotter import load, Volume, save

from brainrender.Utils.data_io import load_json, load_volume_file, listdir, load_mesh_from_file
from brainrender.atlases.base import Atlas
from brainrender.Utils.image import marching_cubes_to_obj


class SBA(Atlas):

    atlas_name = "SBA"
    mesh_format = 'vtk'

    def __init__(self, atlas_folder=None, base_dir=None, **kwargs):
        """
            :param atlas_folder: path to folder with atlas data. The folder content must include:
                    - volumetric data (e.g. as .nii)
                    - label to acronym look up file (lbl_to_acro.json)
                    - label to rgb look up file (lbl_to_rgb.json)
                    - label to full name look up file (lbl_to_name.json)

                    Optionally the folder can contain a .obj file with the root (whole brain) mesh
        """

        Atlas.__init__(self, base_dir=base_dir, **kwargs)

        # Get folder content
        if not os.path.isdir(atlas_folder):
            raise FileNotFoundError(f"The folder passed doesn't exist: {atlas_folder}")

        content = listdir(atlas_folder)
        if not [f for f in content if f.endswith('.nii')]: # TODO expand to support multiple formats
            raise ValueError("Could not find volumetric data")

        if not [f for f in content if "lbl_to_acro.json" in f]:
            raise FileNotFoundError("Could not find file with label to acronym lookup")

        if not [f for f in content if "lbl_to_rgb.json" in f]:
            raise FileNotFoundError("Could not find file with label to color lookup")

        if not [f for f in content if "lbl_to_name.json" in f]:
            raise FileNotFoundError("Could not find file with label to full name lookup")

        self.lbl_to_acro_lookup = load_json([f for f in content if "lbl_to_acro.json" in f][0])
        self.lbl_to_rgb_lookup = load_json([f for f in content if "lbl_to_rgb.json" in f][0])
        self.lbl_to_name_lookup = load_json([f for f in content if "lbl_to_name.json" in f][0])

        self.volume_data = load_volume_file([f for f in content if f.endswith('.nii')][0])

        if [f for f in content if f.endswith(".obj")]:
            if len([f for f in content if f.endswith(".obj")]) > 1:
                raise ValueError("Found too many obj file")
            self.root = load([f for f in content if f.endswith(".obj")][0])

        # Get metadata and prep other stuff
        self.prep_brain_metadata()
        self.meshes_folder = os.path.join(atlas_folder, 'meshes')
        if not os.path.isdir(self.meshes_folder):
            os.mkdir(self.meshes_folder)


    def prep_brain_metadata(self):
        """
            Organises brain and regions metadata 
        """
        self.structures = pd.DataFrame(dict(
            ids = [int(l) for l in self.lbl_to_acro_lookup.keys()]+[-1],
            acronym = [l for l in self.lbl_to_acro_lookup.values()]+['root'],
            color = [ImageColor.getrgb("#"+c) for c in self.lbl_to_rgb_lookup.values()] + [ImageColor.getrgb('#d3d3d3')],
            name = [l for l in self.lbl_to_name_lookup.values()]+ ['root'],
        ))
        self.structures = self.structures.loc[self.structures.ids != 0]

        self.region_acronyms = list(self.structures['acronym'])
        self.regions = list(self.structures['name'])


    def save_structure_mesh(self, acronym, obj_path):
        if acronym == "root":
            volume_data = self.volume_data
            lbl=1.1
        else:
            lbl = self.structures.loc[self.structures.acronym == acronym].ids.values[0]
            volume_data = np.zeros_like(self.volume_data)
            volume_data[self.volume_data == lbl ] = lbl

        print(f"Loading mesh data for {acronym}")

        # Extract surface from volume data
        # verts, faces, normals, values = \
        #         measure.marching_cubes_lewiner(volume_data, .1, step_size=1)
        # faces = faces + 1
        # marching_cubes_to_obj((verts, faces, normals, values), obj_path)

        vol = Volume(volume_data).isosurface(threshold=lbl-.1).smoothLaplacian(edgeAngle=30, featureAngle=90)

        save(vol, obj_path)
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
        if region not in list(self.structures['acronym']):
            print(f"Acronym {region} not in available regions: {self.structures}")
            return None

        # Get obj file path
        obj_path = os.path.join(self.meshes_folder, "{}.vtk".format(region))

        # Load
        if self._check_obj_file(region, obj_path):
            mesh = load_mesh_from_file(obj_path, **kwargs)
            return mesh
        else:
            mesh = self.save_structure_mesh(region, obj_path)
            return mesh

    def _check_valid_region_arg(self, region):
        """
        Check that the string passed is a valid brain region name.
        """
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
        obj_file = obj_file.replace(".obj", ".vtk")
        if not os.path.isfile(obj_file):
            self.save_structure_mesh(region, obj_file)
        return True

    def get_region_color(self, regions):
        """
        Gets the RGB color of a brain region from the Allen Brain Atlas.

        :param regions:  list of regions acronyms.

        """
        if not isinstance(regions, list):
            if not self._check_valid_region_arg(regions):
                return None
            return self.structures.loc[self.structures.acronym == regions].color.values[0]
        else:
            colors = []
            for region in regions:
                if not self._check_valid_region_arg(region):
                    return None
                colors.append(self.structures.loc[self.structures.acronym == region].color.values[0])
            return colors





