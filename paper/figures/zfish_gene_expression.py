from rich import print
import sys
from pathlib import Path

from brainrender import Scene
from brainrender.actors import Volume
from myterial import purple_dark as gene2_color
from myterial import purple_light as gene1_color

sys.path.append("./")
from paper.figures import INSET


print("[bold red]Running: ", Path(__file__).name)


"""
    Data downloaded from: https://fishatlas.neuro.mpg.de/lines/
    for this line: https://zfin.org/ZDB-ALT-050728-2

    data/T_AVG_brn3c_GFP.obj
    data/T_AVG_nk1688CGt_GFP.obj

    converted from volumetric data to mesh with
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
"""
# shift parameters to adjust meshes position
SHIFT = [-20, 15, 30]  # fine tune pos

# camera parameters
cam = {
    "pos": (-835, -1346, 1479),
    "viewup": (0, -1, 0),
    "clippingRange": (1703, 3984),
    "focalPoint": (334, 200, -342),
    "distance": 2660,
}

# create scene
scene = Scene(
    atlas_name="mpin_zfish_1um",
    inset=INSET,
    screenshots_folder="paper/screenshots",
)
scene.root.alpha(0.2)

# add custom meshes from file, but don't show them (alpha=0)
m = scene.add("paper/data/T_AVG_nk1688CGt_GFP.obj", color=gene1_color, alpha=0)
m2 = scene.add("paper/data/T_AVG_brn3c_GFP.obj", color=gene2_color, alpha=0)

# adjust meshes position
for mesh in (m, m2):
    mesh.mesh.addPos(dp_x=SHIFT)

# convert meshes to volumetric data showing gene expression density
vol1 = Volume(m.density(), as_surface=True, min_value=20000, cmap="Reds")
vol1.lw(1)
scene.add(vol1)


vol2 = Volume(m2.density(), as_surface=True, min_value=600, cmap="Blues")
vol2.lw(1)
scene.add(vol2)

# render
scene.render(camera=cam, zoom=2.5)
scene.screenshot(name="zfish_gene_expression")
