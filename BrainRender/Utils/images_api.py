""" ------------------------------
    SET OF FUNCTIONS TO VISUALIZE AND DOWNLOAD IMAGES FROM ALLEN MOUSE BRAIN DATASETS
""" 
# %%
import sys
sys.path.append('./')

import os
import pandas as pd
from tqdm import tqdm

from allensdk.api.queries.svg_api import SvgApi
from allensdk.api.queries.image_download_api import ImageDownloadApi
from allensdk.api.queries.annotated_section_data_sets_api import AnnotatedSectionDataSetsApi
from allensdk.api.queries.ontologies_api import OntologiesApi

from BrainRender.Utils.data_io import send_query, connected_to_internet

# %%
class ImageDownload(SvgApi, ImageDownloadApi):
    # useful tutorial: https://allensdk.readthedocs.io/en/latest/_static/examples/nb/image_download.html
    def __init__(self):
        SvgApi.__init__(self)           # https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/svg_api.py
        ImageDownloadApi.__init__(self) # https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/image_download_api.py 
        self.annsetsapi =   AnnotatedSectionDataSetsApi()       # https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/annotated_section_data_sets_api.py
        self.oapi = OntologiesApi() # https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/ontologies_api.py
        
        # Get metadata about atlases
        self.atlases = pd.DataFrame(self.oapi.get_atlases_table())
        self.atlases_names = sorted(list(self.atlases['name'].values))

        self.mouse_coronal_atlas_id = int(self.atlases.loc[self.atlases['name'] == "Mouse, P56, Coronal"].id.values[0])
        self.mouse_sagittal_atlas_id = int(self.atlases.loc[self.atlases['name'] == "Mouse, P56, Sagittal"].id.values[0])
        self.mouse_3D_atlas_id = int(self.atlases.loc[self.atlases['name'] == "Mouse, Adult, 3D Coronal"].id.values[0])


        # Get metadata about products
        if connected_to_internet():
            self.products = pd.DataFrame(send_query("http://api.brain-map.org/api/v2/data/query.json?criteria=model::Product"))
            self.mouse_brain_reference_product_id = 12
            self.mouse_brain_ish_data_product_id = 1
            self.products_names = sorted(list(self.products["name"].values))
            self.mouse_products_names = sorted(list(self.products.loc[self.products.species == "Mouse"]["name"].values))
        else:
            raise ConnectionError("It seems that you are not connected to the internet, you won't be able to download stuff.")

    # UTILS
    def get_atlas_by_name(self, atlas_name):
        if not atlas_name in self.atlases_names: raise ValueError("Available atlases: {}".format(self.atlases_names))
        return self.atlases.loc[self.atlases['name'] == atlas_name].id.values[0]


    def get_products_by_species(self, species):
        return self.products.loc[self.products.species == species]

    def get_experimentsid_by_productid(self, productid, **kwargs):
        # for more details: https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/image_download_api.py
        return pd.DataFrame(self.get_section_data_sets_by_product([productid], **kwargs))

    def get_experimentimages_by_expid(self, expid):
        # expid should be a section dataset id
        return pd.DataFrame(self.section_image_query(expid))

    def get_atlasimages_by_atlasid(self, atlasid):
        if not isinstance(atlasid, int): 
            raise ValueError("Atlas id should be an integer not: {}".format(atlasid))
        return pd.DataFrame(self.atlas_image_query(atlasid))

    def download_images_by_imagesid(self, savedir, imagesids, downsample=0, annotated=True, atlas_svg=True):
        if not os.path.isdir(savedir):
            os.mkdir(savedir)
        
        curdir = os.getcwd()
        os.chdir(savedir)

        for imgid in tqdm(imagesids):
            if not atlas_svg and not annotated:
                savename = str(imgid)+".jpg"
            elif not atlas_svg and annotated:
                savename = str(imgid)+"_annotated.jpg"
            else:
                savename = str(imgid)+".svg"

            if os.path.isfile(savename): continue

            if not atlas_svg and not annotated:
                self.download_section_image(imgid, file_path=savename, downsample=downsample)
            elif not atlas_svg and annotated:
                self.download_atlas_image(imgid, file_path=savename, annotation=True, downsample=downsample)
            else:
                self.download_svg(imgid, file_path=savename)

        file_names = os.listdir(savedir)
        print("Downloaded {} images".format(len(file_names)))
        os.chdir(curdir)

    def download_images_by_atlasid(self, savedir, atlasid, **kwargs):
        imgsids = sorted(list(self.get_atlasimages_by_atlasid(atlasid)['id']))
        self.download_images_by_imagesid(savedir, imgsids, **kwargs)


imgd = ImageDownload()

# %%
# Products are the different types of experiments performed by allen
path = "/Users/federicoclaudi/Dropbox (UCL - SWC)/Rotation_vte/Presentations/atlases/allen_mouse_coronal"
imgd.download_images_by_atlasid(path, imgd.mouse_coronal_atlas_id, atlas_svg=True)


#%%
