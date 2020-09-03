# # %%
# from brainrender.Utils.webqueries import send_query


# url = 'http://api.brain-map.org/api/v2/reference_to_image/10.json?x=6085&y=3670&z=4883&section_data_set_ids=68545324,67810540'

# send_query(url)

# # %%
# from brainrender.ABA.atlas_images import ImageDownload
# # %%
# api = ImageDownload()
# api.get_atlas_by_name(api.mouse_coronal)
# api.get_atlas_dataset_id_by_name(api.mouse_coronal)
# # %%
# id = int(api.get_atlas_by_name(api.mouse_coronal))
# api.get_atlasimages_by_atlasid(id)['data_set_id'].values[0]

# # %%
# url = 'http://api.brain-map.org/api/v2/reference_to_image/10.json?x=6085&y=3670&z=4883&section_data_set_ids=100048576'

# send_query(url)
# # %%
# api.download_images_by_imagesid('', [100960276], downsample=4, atlas_svg=False)
# %%

from brainrender.scene import Scene
import numpy as np

scene = Scene()

img = scene.plotter.load("100960276_annotated.jpg")

img.rotateY(90).rotateX(180).scale(18).mirror(axis="x")

bounds = img.bounds()

atlas_shape = np.array(scene.atlas.metadata["shape"]) * np.array(
    scene.atlas.metadata["resolution"]
)

x, y, z = atlas_shape
center = scene.root.centerOfMass()


img.pos(x=6085, y=center[1] + y / 2, z=center[2] - z / 2)


print(scene.root.centerOfMass())

scene.add_actor(img)

scene.add_sphere_at_point([6085, 3670, 4883])
scene.render()
# %%
