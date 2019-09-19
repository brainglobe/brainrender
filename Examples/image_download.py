# %%
from allensdk.api.queries.image_download_api import ImageDownloadApi
from allensdk.api.queries.svg_api import SvgApi
from allensdk.config.manifest import Manifest

import matplotlib.pyplot as plt
from skimage.io import imread
import pandas as pd

import logging
import os
from base64 import b64encode

from IPython.display import HTML, display
%matplotlib inline

images_fld = "D:\\Dropbox (UCL - SWC)\\Rotation_vte\\analysis_metadata\\anatomy\\ABA_Images"

#%%
def verify_image(file_path, figsize=(18, 22)):
    image = imread(file_path)

    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(image)
    
    
def verify_svg(file_path, width_scale, height_scale):
    # we're using this function to display scaled svg in the rendered notebook.
    # we suggest that in your own work you use a tool such as inkscape or illustrator to view svg
    
    with open(file_path, 'rb') as svg_file:
        svg = svg_file.read()
    encoded_svg = b64encode(svg)
    decoded_svg = encoded_svg.decode('ascii')
    
    st = r'<img class="figure" src="data:image/svg+xml;base64,{}" width={}% height={}%></img>'.format(decoded_svg, width_scale, height_scale)
    display(HTML(st))

#%%


image_api = ImageDownloadApi()
svg_api = SvgApi()



#%%
# Download a cytoarchitecture image

section_image_id = 70945123
file_path = os.path.join(images_fld, '70945123.jpg')
downsample = 3
image_api.download_section_image(section_image_id, file_path, downsample=downsample)
verify_image(file_path)



#%%
# Download experiment images


section_image_id = 297225716
file_path = os.path.join(images_fld, '297225716_connectivity.jpg')
downsample = 3
ranges = image_api.get_section_image_ranges([section_image_id])[0]


image_api.download_projection_image(section_image_id, file_path, downsample=downsample, 
                        ranges=None, # can be used to normalize image colors
                        projection=True)  # projection True download a mask with just fluorescent pixels

verify_image(file_path)



#%%
# Download annotated images as SVG
svg_api = SvgApi()
atlas_image_id = 100883954
# file_path = os.path.join(images_fld, '576990983.jpg')

# # download annotated image
# image_api.download_atlas_image(atlas_image_id, file_path, annotation=True, downsample=downsample)
# verify_image(file_path)

# download SVG
file_path = os.path.join(images_fld, '100883954.svg')

svg_api.download_svg(atlas_image_id, file_path=file_path)
verify_svg(file_path, 35, 35)


#%%


atlas_id = 602630314  # this should be the mouse coronal section_image_id
# 602630314 coronal
# 2 sagitattal atlas

# image_api.section_image_query(section_data_set_id) is the analogous method for section data sets
atlas_image_records = image_api.atlas_image_query(atlas_id)

# this returns a list of dictionaries. Let's convert it to a pandas dataframe
atlas_image_dataframe = pd.DataFrame(atlas_image_records)

# and use the .head() method to display the first few rows
atlas_image_dataframe.head()



#%%
