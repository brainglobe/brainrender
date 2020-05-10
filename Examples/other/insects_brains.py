import brainrender
brainrender.SHADER_STYLE = 'cartoon'
from brainrender.scene import Scene

from brainrender.atlases.insects_brains_db import IBDB # ! this class is the atlas for insects brains

"""
    In this tutorial you can see how to use brainrender to fetch
    and render 3D rendering of brain regions from a number of insects brains.

    All data is hosted by: https://insectbraindb.org/app/
    Please read their terms of use (https://insectbraindb.org/app/terms)
    Also please refer to the website to find the original source of these datasets

    You can also visualize these data interactively at: https://insectbraindb.org/app/three;controls=true;mode=species
"""

# Create a scene
scene = Scene(atlas=IBDB, # specify that we are using the insects brains databse atlas
               atlas_kwargs=dict(species='Schistocerca gregaria') # Specify which insect species' brain to use
               )

# Print a list of all the brain structures available for this species' brain
print(scene.atlas.structures)


# Add all brain regions in the mushroom body to the rendering
central_complex = ['CBU-S2', 'CBU-S1', 'CBU-S3', 'NO-S3_left',
                            'NO-S2_left',
                            'NO-S2_right',
                            'NO-S3_right',
                            'NO_S1_left',
                            'NO-S1_right',
                            'NO-S4_left',
                            'NO-S4_right', 'CBL', 'PB']

scene.add_brain_regions(central_complex, alpha=1)

scene.render() 