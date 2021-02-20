import h5py
import pandas as pd
import sys
from rich import print
from pathlib import Path
from myterial import salmon as c1
from myterial import orange_darker as c2
from myterial import indigo as c3

from brainrender import Scene
from brainrender.actors import Points

sys.path.append("./")
from paper.figures import INSET

print("[bold red]Running: ", Path(__file__).name)

# camera parameters
cam = {
    "pos": (-890, -1818, 979),
    "viewup": (1, -1, -1),
    "clippingRange": (1773, 4018),
    "focalPoint": (478, 210, -296),
    "distance": 2759,
}

# load cluster data and get cell coordinates
cluster_data = h5py.File("paper/data/zfish_rois_clusters.h5", "r")
cluster_ids = cluster_data["cluster_ids"][:]
roi_coords = cluster_data["coords"][:]

# create scene
scene = Scene(
    inset=INSET,
    screenshots_folder="paper/screenshots",
    atlas_name="mpin_zfish_1um",
)

# add cells colored by cluster
colors = [c1, c2, c3]
for i, col in enumerate(colors):
    rois_in_cluster = roi_coords[cluster_ids == i, :]
    coords = pd.DataFrame(rois_in_cluster, columns=["x", "y", "z"]).values

    pts = scene.add(Points(coords, colors=col, radius=2, alpha=1))
    scene.add_silhouette(pts, lw=1)

# render
scene.render(camera=cam, zoom=2.5)
scene.screenshot(name="zfish_functional_clusters")
