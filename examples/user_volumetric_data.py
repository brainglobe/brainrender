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

from pathlib import Path
import pooch

from brainglobe_space import AnatomicalSpace
from brainglobe_utils.IO.image.load import load_any
from myterial import blue_grey, orange
from rich import print
from vedo import Volume as VedoVolume

from brainrender import Scene

print(f"[{orange}]Running example: {Path(__file__).name}")

download_path = Path.home() / ".brainglobe" / "brainrender" / "example-data"
filename = "T_AVG_s356tTg.tif"
scene = Scene(atlas_name="mpin_zfish_1um")

# for some reason the list of returned by pooch does not seem to be
# in the same order every time
_ = pooch.retrieve(
    url="https://api.mapzebrain.org/media/Lines/brn3cGFP/average_data/T_AVG_s356tTg.zip",
    known_hash="54b59146ba08b4d7eea64456bcd67741db4b5395235290044545263f61453a61",
    path=download_path,
    progressbar=True,
    processor=pooch.Unzip(extract_dir="."),
)

datafile = download_path / filename


# 1. load the data
print("Loading data")
data = load_any(datafile)

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
