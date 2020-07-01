import pandas as pd
import numpy as np
import os
from PIL import ImageColor

from treelib import Tree

from vedo import load, merge, write

import brainrender
from brainrender.Utils.paths_manager import Paths
from brainrender.Utils.webqueries import request
from brainrender.Utils.data_io import load_mesh_from_file

"""
    Class to download and render a number of insect brains from:
    https://insectbraindb.org/app/

    The InsectBrainDB.org is primarily curated by Stanley Heinze

    The insectbraindb.org has a terms of use, which provides guidance on how best to credit data from these repositories. 

    The insectbraindb.org is primarily curated by Dr. Stanley Heinze, and 
    was buily by Kevin Tedore, and has several significant supporters, including the ERC.




    Check Examples/custom_atlases/insects_brains.py for more details.

"""


class IBDB(Paths):

    atlas_name = "InsectBrains"
    mesh_format = "obj"

    _base_url = "https://insectbraindb.org"
    _url_paths = dict(
        brain_info="archive/species/most_current_permitted/?species_id=",
        species_info="api/species/min/",
        data="https://s3.eu-central-1.amazonaws.com/ibdb-file-storage",
        structures_tree="https://insectbraindb.org/api/structures/list_hierarchy",
    )

    default_camera = dict(
        position=[1035.862, 420.237, -3058.244],
        focal=[1253.28, 759.97, 428.418],
        viewup=[0.03, -0.995, 0.095],
        distance=3509.914,
        clipping=[2616.137, 4643.461],
    )

    def __init__(
        self, species=None, sex=None, base_dir=None, make_root=True, **kwargs
    ):
        self.make_root = make_root

        Paths.__init__(self, base_dir=base_dir, **kwargs)

        # Get a list of available species
        self.species_info = pd.DataFrame(
            request(
                f"{self._base_url}/{self._url_paths['species_info']}"
            ).json()
        )
        self.species = list(self.species_info.scientific_name.values)

        # Get selected species
        self.structures, self.region_names, self.region_acronyms = (
            None,
            None,
            None,
        )
        self.sel_species = species
        self.sex = sex
        self.get_brain(species=species, sex=sex)

    def get_brain_id_from_species_name(self, sel_species):
        if sel_species not in self.species:
            raise ValueError(
                f"The species {sel_species} is not among the available species {self.species}"
            )

        try:
            brain_id = self.species_info.loc[
                self.species_info.scientific_name == sel_species
            ]["id"].values[0]
        except:
            raise ValueError(
                f"Could not find brain data for species {sel_species}\n"
                + f"available species:\n{self.species_info}"
            )
        return brain_id

    def get_structures_hierarchy(self):
        def add_descendants_to_tree(tree, structure, parent_id=None):
            """
                Recursively goes through all the the descendants of a region and adds them to the tree
            """
            if parent_id is not None:
                tree.create_node(
                    tag=structure["name"],
                    identifier=structure["id"],
                    parent=parent_id,
                )
            else:
                tree.create_node(
                    tag=structure["name"], identifier=structure["id"],
                )

            if "children" not in structure.keys():
                return
            if structure["children"]:
                for child in structure["children"]:
                    add_descendants_to_tree(tree, child, structure["id"])

        structures_hierarchy = request(
            self._url_paths["structures_tree"]
        ).json()

        tree = Tree()
        tree.create_node(
            tag="root", identifier=0,
        )
        for supercategory in structures_hierarchy:
            add_descendants_to_tree(tree, supercategory, 0)

        self.structures_hierarchy = tree

    def get_structures_reconstructions(self, species, sex):
        iid = self.get_brain_id_from_species_name(species)

        data = request(
            f"{self._base_url}/{self._url_paths['brain_info']}{iid}"
        ).json()
        if not len(data):
            print("Could not get any data for this brain")
            return None

        reconstructions = [r["viewer_files"] for r in data["reconstructions"]]
        if not reconstructions:
            print(f"No data was found for {species}")
            return

        n_elems = [len(rec) for rec in reconstructions]

        if sex is None:
            try:
                sex = np.argmax(n_elems)
            except:
                raise ValueError("No data retrieved")

        if not n_elems[sex]:
            raise ValueError(f"No reconstructions found for {sex} {species}")
        else:
            reconstruction = reconstructions[sex]

        # Get data about the brain regions
        structures = dict(
            name=[],
            acronym=[],
            color=[],
            obj_path=[],
            hemisphere=[],
            parent=[],
            children=[],
        )

        for d in reconstruction:
            if "structures" not in d.keys():
                continue
            if not d["structures"]:
                continue

            hemi = d["structures"][0]["hemisphere"]
            if hemi is None:
                hemi = "both"

            if hemi == "right":
                name = d["structures"][0]["structure"]["name"] + "_R"
            elif hemi == "left":
                name = d["structures"][0]["structure"]["name"] + "_L"
            else:
                name = d["structures"][0]["structure"]["name"]

            abbr = d["structures"][0]["structure"]["abbreviation"]
            acro = (
                abbr + d["p_file"]["file_name"].split(abbr)[-1].split(".")[0]
            )

            if "_left" in acro:
                acro = acro.split("_left")[0] + "_left"
            elif "_right" in acro:
                acro = acro.split("_right")[0] + "_right"

            structures["obj_path"].append(d["p_file"]["path"])
            structures["hemisphere"].append(hemi.lower())

            structures["name"].append(name)
            structures["acronym"].append(acro)
            structures["color"].append(
                d["structures"][0]["structure"]["color"]
            )

            structures["parent"].append(
                d["structures"][0]["structure"]["parent"]
            )
            structures["children"].append(
                d["structures"][0]["structure"]["children"]
            )

        self.structures = pd.DataFrame(structures)

    def get_brain(self, species=None, sex=None):
        # Get metadata about the brain from database
        if species is None:
            species = self.sel_species

        if species is None:
            print("No species name passed")
            return None

        self.species = species
        self.sex = sex

        # Get reconstructions and metadata
        self.get_structures_hierarchy()
        self.get_structures_reconstructions(species, sex)

        # Prep some vars
        self.region_acronyms = list(self.structures["acronym"])
        self.regions = list(self.structures["name"])

        meshes_fld = os.path.join(self.ibdb_meshes_folder, self.species)
        if not os.path.isdir(meshes_fld):
            print("Creating folder at: {}".format(meshes_fld))
            os.makedirs(meshes_fld)
        self.meshes_folder = meshes_fld

        if self.make_root:
            self.make_root_mesh()

    def download_and_write_mesh(self, acronym, obj_path):
        print(f"Downloading mesh data for {acronym}")
        path = self.structures.loc[
            self.structures.acronym == acronym
        ].obj_path.values[0]
        url = f"{self._url_paths['data']}/{path}"

        # download and write .obj
        mesh_data = request(url).content.decode("utf-8").split("\n")
        with open(obj_path, "w") as f:
            for md in mesh_data:
                f.write(f"{md}\n")
            f.close()

        # return the vtk actor
        return load(obj_path)

    def make_root_mesh(self):
        if self.structures is None:
            return

        obj_path = os.path.join(self.meshes_folder, "root.vtk")
        if os.path.isfile(obj_path):
            return

        # Get the mesh for each brain region to create root
        meshes = [
            self._get_structure_mesh(reg) for reg in self.region_acronyms
        ]
        root = merge(meshes)
        write(root, obj_path)

    # ---------------------------------------------------------------------------- #
    #                          Replace base atlas methods                          #
    # ---------------------------------------------------------------------------- #

    def _get_structure_mesh(self, acronym, **kwargs):
        """
        Fetches the mesh for a brain region from the atlas.

        :param acronym: string, acronym of brain region
        :param **kwargs:

        """
        if self.structures is None:
            print("No atlas was loaded, use self.get_brain first")
            return None

        if acronym not in self.region_acronyms and acronym != "root":
            raise ValueError(
                f"Acronym {acronym} not in available regions: {self.structures}"
            )

        # Get obj file path
        if acronym != "root":
            mesh_format = self.mesh_format
        else:
            mesh_format = "vtk"
        obj_path = os.path.join(
            self.meshes_folder, "{}.{}".format(acronym, mesh_format)
        )

        # Load
        if self._check_obj_file(acronym, obj_path):
            mesh = load_mesh_from_file(obj_path, **kwargs)
            return mesh
        else:
            mesh = self.download_and_write_mesh(acronym, obj_path)
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
        If the .obj file for a brain region hasn't been downloaded already, this function downloads it and writes it.

        :param region: string, acronym of brain region
        :param obj_file: path to .obj file to write downloaded data.

        """
        # checks if the obj file has been downloaded already, if not it takes care of downloading it
        if not os.path.isfile(obj_file):
            self.download_and_write_mesh(region, obj_file)
        return True

    def get_region_color(self, regions):
        """
        Gets the RGB color of a brain region from the atlas.

        :param regions:  list of regions acronyms.

        """
        if not isinstance(regions, list):
            if not self._check_valid_region_arg(regions):
                return None
            return ImageColor.getrgb(
                self.structures.loc[
                    self.structures.acronym == regions
                ].color.values[0]
            )
        else:
            colors = []
            for region in regions:
                if not self._check_valid_region_arg(region):
                    return None
                colors.append(
                    ImageColor.getrgb(
                        self.structures.loc[
                            self.structures.acronym == region
                        ].color.values[0]
                    )
                )
            return colors

    def get_brain_regions(
        self,
        brain_regions,
        alpha=None,
        colors=None,
        use_original_color=True,
        **kwargs,
    ):
        if alpha is None:
            alpha = brainrender.DEFAULT_STRUCTURE_ALPHA

        if not isinstance(brain_regions, (list, tuple)):
            brain_regions = [brain_regions]

        # check the colors input is correct
        if not use_original_color:
            if colors is None:
                colors = [
                    brainrender.DEFAULT_STRUCTURE_COLOR
                    for reg in brain_regions
                ]
            else:
                if isinstance(colors, (list, tuple)):
                    if len(colors) != len(brain_regions):
                        raise ValueError("Wrong number of colors")
                else:
                    colors = [colors for reg in brain_regions]
        else:
            colors = [self.get_region_color(reg) for reg in brain_regions]

        actors = {}
        for region, color in zip(brain_regions, colors):
            actors[region] = self._get_structure_mesh(region, c=color)

        return actors
