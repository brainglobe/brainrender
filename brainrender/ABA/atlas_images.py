""" ------------------------------
    SET OF FUNCTIONS TO VISUALIZE AND DOWNLOAD IMAGES FROM ALLEN MOUSE BRAIN DATASETS:
        - Download images from experiments (e.g. ISH gene expression images)
        - Download SVG/PNG version of the Allen Brain Atlas images (for any atlas)
"""
import sys

sys.path.append("./")

from pathlib import Path
from os import chdir
import pandas as pd
from rich.progress import track

from allensdk.api.queries.svg_api import SvgApi
from allensdk.api.queries.image_download_api import ImageDownloadApi
from allensdk.api.queries.annotated_section_data_sets_api import (
    AnnotatedSectionDataSetsApi,
)
from allensdk.api.queries.ontologies_api import OntologiesApi

from brainrender.Utils.webqueries import send_query
from brainrender.Utils.decorators import fail_on_no_connection


class ImageDownload(SvgApi, ImageDownloadApi):
    """ 
    Handles query to the Allen ImageDownloadApi and saves the data
    """

    mouse_coronal = "Mouse, P56, Coronal"
    mouse_sagittal = "Mouse, P56, Sagittal"
    mouse3d = "Mouse, Adult, 3D Coronal"

    # useful tutorial: https://allensdk.readthedocs.io/en/latest/_static/examples/nb/image_download.html
    @fail_on_no_connection
    def __init__(self):
        SvgApi.__init__(
            self
        )  # https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/svg_api.py
        ImageDownloadApi.__init__(
            self
        )  # https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/image_download_api.py
        self.annsetsapi = (
            AnnotatedSectionDataSetsApi()
        )  # https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/annotated_section_data_sets_api.py
        self.oapi = (
            OntologiesApi()
        )  # https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/ontologies_api.py

        # Get metadata about atlases
        self.atlases = pd.DataFrame(self.oapi.get_atlases_table())
        self.atlases_names = sorted(list(self.atlases["name"].values))

        self.mouse_coronal_atlas_id = int(
            self.atlases.loc[
                self.atlases["name"] == self.mouse_coronal
            ].id.values[0]
        )
        self.mouse_sagittal_atlas_id = int(
            self.atlases.loc[
                self.atlases["name"] == self.mouse_sagittal
            ].id.values[0]
        )
        self.mouse_3D_atlas_id = int(
            self.atlases.loc[self.atlases["name"] == self.mouse3d].id.values[0]
        )

        # Get metadata about products
        self.products = pd.DataFrame(
            send_query(
                "http://api.brain-map.org/api/v2/data/query.json?criteria=model::Product"
            )
        )
        self.mouse_brain_reference_product_id = 12
        self.mouse_brain_ish_data_product_id = 1
        self.products_names = sorted(list(self.products["name"].values))
        self.mouse_products_names = sorted(
            list(
                self.products.loc[self.products.species == "Mouse"][
                    "name"
                ].values
            )
        )

    # UTILS
    def get_atlas_by_name(self, atlas_name):
        """
        Get a brain atlas in the Allen's database given it's name

        :param atlas_name: str with atlas name

        """
        if atlas_name not in self.atlases_names:
            raise ValueError(
                "Available atlases: {}".format(self.atlases_names)
            )
        return self.atlases.loc[self.atlases["name"] == atlas_name].id.values[
            0
        ]

    def get_products_by_species(self, species):
        """
        Get all 'products' in the Allen Database for a given species

        :param species: str

        """
        return self.products.loc[self.products.species == species]

    def get_experimentsid_by_productid(self, productid, **kwargs):
        """
        Get the experiment's ID that belong to the same project (product).

        :param productid: int with product ID number
        :param **kwargs: 

        """
        # for more details: https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/image_download_api.py
        return pd.DataFrame(
            self.get_section_data_sets_by_product([productid], **kwargs)
        )

    def get_experimentimages_by_expid(self, expid):
        """
        Get's images that belong to an experiment

        :param expid: int with experiment name. 

        """
        # expid should be a section dataset id
        return pd.DataFrame(self.section_image_query(expid))

    def get_atlasimages_by_atlasid(self, atlasid):
        """
        Get the metadata of images that belong to an atlas. 

        :param atlasid: int with atlas number

        """
        if not isinstance(atlasid, int):
            raise ValueError(
                "Atlas id should be an integer not: {}".format(atlasid)
            )
        return pd.DataFrame(self.atlas_image_query(atlasid))

    def download_images_by_imagesid(
        self,
        savedir,
        imagesids,
        downsample=0,
        annotated=True,
        snames=None,
        atlas_svg=True,
    ):
        """
        Downloads and saves images given a list of images IDs. 


        :param savedir: str, folder in which to save the image
        :param imagesids: list of int with images IDs
        :param downsample: downsample factor, to reduce the image size and resolution (Default value = 0)
        :param annotated: if True the images are overlayed with annotations  (Default value = True)
        :param snames: if True the images are overlayed with the structures names (Default value = None)
        :param atlas_svg: if True fetches the images as SVG, otherwise as PNG (Default value = True)

        """
        savedir = Path(savedir)
        savedir.mkdir(exist_ok=True)

        curdir = Path.cwd()
        chdir(savedir)

        for i, imgid in track(
            enumerate(imagesids),
            total=len(imagesids),
            description="downloading iamges...",
        ):
            if not atlas_svg and not annotated:
                savename = str(imgid) + ".jpg"
            elif not atlas_svg and annotated:
                savename = str(imgid) + "_annotated.jpg"
            else:
                savename = str(imgid) + ".svg"

            if snames is not None:
                sname, ext = savename.split(".")
                savename = (
                    sname + "_sect{}_img{}.".format(snames[i], i + 1) + ext
                )

            if Path(savename).exists():
                continue

            if not atlas_svg and not annotated:
                self.download_section_image(
                    imgid, file_path=savename, downsample=downsample
                )
            elif not atlas_svg and annotated:
                self.download_atlas_image(
                    imgid,
                    file_path=savename,
                    annotation=True,
                    downsample=downsample,
                )
            else:
                self.download_svg(imgid, file_path=savename)

        chdir(curdir)

    def download_images_by_atlasid(
        self, savedir, atlasid, debug=False, **kwargs
    ):
        """
        Downloads all the images that belong to an altlas

        :param savedir: str, folder in which to save the images
        :param atlasid: int, ID of the atlas to use
        :param **kwargs: keyword arguments for self.download_images_by_imagesid

        """
        imgsids = self.get_atlasimages_by_atlasid(atlasid)["id"]

        if debug:  # use fewer images to speed up
            imgsids = imgsids[:2]

        imgs_secs_n = self.get_atlasimages_by_atlasid(atlasid)[
            "section_number"
        ]

        _ = kwargs.pop("snames", None)

        self.download_images_by_imagesid(
            savedir, imgsids, snames=imgs_secs_n, **kwargs
        )
