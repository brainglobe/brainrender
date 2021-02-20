from brainrender import Scene
from brainrender.actors import Points
import h5py
import pandas as pd
import sys

from myterial import salmon as c1
from myterial import orange_darker as c2
from myterial import indigo as c3

sys.path.append("./")
from scripts.settings import INSET
from rich import print

print("[bold red]Running: ", __name__)


cam = {
    "pos": (-890, -1818, 979),
    "viewup": (1, -1, -1),
    "clippingRange": (1773, 4018),
    "focalPoint": (478, 210, -296),
    "distance": 2759,
}


cluster_data = h5py.File("data/zfish_rois_clusters.h5", "r")
cluster_ids = cluster_data["cluster_ids"][:]
roi_coords = cluster_data["coords"][:]

# -------------------------------- make scene -------------------------------- #
scene = Scene(
    inset=INSET, screenshots_folder="figures", atlas_name="mpin_zfish_1um"
)

colors = [c1, c2, c3]
for i, col in enumerate(colors):
    rois_in_cluster = roi_coords[cluster_ids == i, :]
    coords = pd.DataFrame(rois_in_cluster, columns=["x", "y", "z"]).values

    pts = scene.add(Points(coords, colors=col, radius=2, alpha=1))
    scene.add_silhouette(pts, lw=1)


scene.render(camera=cam, zoom=2.5)
scene.screenshot(name="zfish_functional_clusters")
