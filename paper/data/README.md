# cell-detect-paper-cells.h5
See cellfinder preprint Fig4

# CC_134_1_ch1inj
smth CRE mouse injected in tdTomato mice

# EM neurons
First head to https://microns-explorer.org/phase1, to download the dataset (it's about 10GB)

Then use create_neurons_objs.py to extract meshes for the reconstruction of individual neurons. This script will create a .obj file for each neuron to make it easier to render them at a later stage, but it will take a while to complete.

Finally you can use visualize_neurons.py to create a brainrender scene and populate it with the meshes for individual neurons. There's a few variables and parameter you can tweak to get different rendering styles.

# Mouse gene expression
from allen

# Injections from me

# Zebrafish gene expression
Data downloaded from: https://fishatlas.neuro.mpg.de/lines/
for this line: https://zfin.org/ZDB-ALT-050728-2

data/T_AVG_brn3c_GFP.obj
data/T_AVG_nk1688CGt_GFP.obj

converted to mesh with
```python

    from brainio import brainio
    from vedo import Volume, write
    from bg_space import AnatomicalSpace
    from brainrender import Scene

    fp ='/Users/federicoclaudi/Downloads/T_AVG_Chat_GFP.tif'
    data = brainio.load_any(fp)

    s = Scene(atlas_name='mpin_zfish_1um')

    source_space = AnatomicalSpace("rai")
    target_space = s.atlas.space
    transformed_stack = source_space.map_stack_to(target_space, data)

    vol = Volume(transformed_stack, origin=s.root.origin()).medianSmooth()

    mesh = vol.isosurface().c('red').decimate().clean()
    write(mesh, 'data/T_AVG_Chat_GFP.obj')
```