"""

    This example shows how to render VOLUMETRIC data in brainrender.
    It uses data downloaded from: https://fishatlas.neuro.mpg.de/lines/
    showing gene expression for this transgenic line (brn3c:GPF): https://zfin.org/ZDB-ALT-050728-2

    These data are a 3D image with orientation different from the axes system used by
    brainrender, so it has to be loaded and transposed to the correct orientation

    This examples shows how to:
        - load volumetric data from a TIFF file
        - transpose the data with BrainGlobe Space to re-orient it
        - extract a mesh from the volumetric data using vedo
        - render the data

"""

try:
    import imio
except ImportError:
    raise ImportError(
        'You need imio to run this example: "pip install imio".\nFor more details: https://github.com/brainglobe/imio'
    )

from bg_space import AnatomicalSpace
from vedo import Volume
from brainrender import Scene
from pathlib import Path
from myterial import blue_grey


from rich import print
from myterial import orange

print(f"[{orange}]Running example: {Path(__file__).name}")

# specify where the data are saved
datafile = Path("/Users/federicoclaudi/Downloads/T_AVG_brn3c_GFP.tif")

if not datafile.exists():
    raise ValueError(
        "Before running this example you need to download the data for gene expression of the line brn3c:GFP from https://fishatlas.neuro.mpg.de/lines/"
    )


# 1. load the data
print("Loading data")
data = imio.load.load_any(datafile)

# 2. aligned the data to the scene's atlas' axes
print("Transforming data")
scene = Scene(atlas_name="mpin_zfish_1um")

source_space = AnatomicalSpace(
    "ira"
)  # for more info: https://docs.brainglobe.info/bg-space/usage
target_space = scene.atlas.space
transformed_stack = source_space.map_stack_to(target_space, data)

# 3. create a Volume vedo actor and smooth
print("Creating volume")
vol = Volume(transformed_stack, origin=scene.root.origin()).medianSmooth()


# 4. Extract a surface mesh from the volume actor
print("Extracting surface")
SHIFT = [-20, 15, 30]  # fine tune mesh position
mesh = (
    vol.isosurface(threshold=20).c(blue_grey).decimate().clean().addPos(*SHIFT)
)

# 5. render
print("Rendering")
scene.add(mesh)
scene.render(zoom=13)
