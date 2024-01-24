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

from pathlib import Path
import pooch

from brainglobe_space import AnatomicalSpace
from myterial import blue_grey, orange
from rich import print
from vedo import Volume as VedoVolume

from brainrender import Scene
from brainrender.actors import Volume

print(f"[{orange}]Running example: {Path(__file__).name}")

# specify where the data are saved

retrieved_paths = pooch.retrieve(
    url="https://api.mapzebrain.org/media/Lines/brn3cGFP/average_data/T_AVG_s356tTg.zip",
    known_hash="54b59146ba08b4d7eea64456bcd67741db4b5395235290044545263f61453a61",
    path=Path.home()
    / ".brainglobe"
    / "brainrender-example-data",  # zip will be downloaded here
    progressbar=True,
    processor=pooch.Unzip(
        extract_dir=""
        # path to unzipped dir,
        # *relative* to the path set in 'path'
    ),
)

datafile = Path(retrieved_paths[1])  # [0] is zip file

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
)  # for more info: https://docs.brainglobe.info/brainglobe-space/usage
target_space = scene.atlas.space
transformed_stack = source_space.map_stack_to(target_space, data)

# 3. create a Volume vedo actor and smooth
print("Creating volume")
vol = VedoVolume(transformed_stack)
vol.smooth_median()


# 4. Extract a surface mesh from the volume actor
print("Extracting surface")
mesh = vol.isosurface(value=20).c(blue_grey).decimate().clean()
SHIFT = [30, 15, -20]  # fine tune mesh position
current_position = mesh.pos()
new_position = [SHIFT[i] + current_position[i] for i in range(3)]
mesh.pos(*new_position)

# 5. render
print("Rendering")
scene.add(mesh)
scene.render(zoom=13)
