from brainrender import Scene
from brainrender.atlas_specific import get_streamlines_for_region
from brainrender.actors.streamlines import make_streamlines
from morphapi.api.mouselight import MouseLightAPI
from brainrender.actors import make_neurons
import sys

sys.path.append("./")
from scripts.settings import INSET, SILHOUETTE


from vedo import settings
from rich import print

print("[bold red]Running: ", __name__)

settings.useDepthPeeling = (
    True  # necessary for rendering of semitransparent actors
)
settings.useFXAA = True

cam = {
    "pos": (-19318, -651, -5704),
    # "focalPoint": (9200, 4332, -5680),
    "viewup": (0, -1, 0),
    # "distance": 28950,
    "clippingRange": (19718, 40641),
}
mlapi = MouseLightAPI()


scene = Scene(inset=INSET, screenshots_folder="figures")
scene.root._needs_silhouette = SILHOUETTE
for col, reg in zip(("steelblue", "steelblue"), ("VP", "VAL")):
    streams = get_streamlines_for_region(reg)
    scene.add(*make_streamlines(*streams, color=col, alpha=0.12))

    reg = scene.add_brain_region(
        reg, color=col, alpha=0.1, silhouette=SILHOUETTE
    )
    # reg._silhouette_kwargs["lw"] = 0.5

neurons_metadata = mlapi.fetch_neurons_metadata(
    filterby="soma", filter_regions=["MOs"]
)
to_add = [neurons_metadata[47], neurons_metadata[47]]
neurons = mlapi.download_neurons(to_add)
neurons = scene.add(
    *make_neurons(*neurons, neurite_radius=13, color="#30cf11")
)
if SILHOUETTE:
    scene.add_silhouette(*neurons, lw=0.5, color="k")


print("slicing")
p = scene.atlas.get_region("region", "STR").centerOfMass()
plane = scene.atlas.get_plane(pos=p, plane="frontal")
scene.slice("sagittal")


scene.render(zoom=1.75, camera="sagittal")
# scene.render(zoom=1.5, camera=cam)
scene.screenshot(name="streamlines_th")

scene.close()
