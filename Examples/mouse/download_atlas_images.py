""" 
    This tutorial shows how download images for the allen institute
    mouse brain atlas. 
"""

from brainrender.ABA.atlas_images import ImageDownload

imd = ImageDownload()

# Download coronal atlas as png
fld = "atlas_images"  # pass a path to the folder where you want to save the images
imd.download_images_by_atlasid(
    fld, imd.mouse_coronal_atlas_id, atlas_svg=False
)
