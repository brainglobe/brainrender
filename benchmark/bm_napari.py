import numpy as np
import napari

from benchmark.timer import SimpleTimer
from brainrender import Scene

"""
    Compare performance on napari
"""

# get a couple meshes with brainrender
scene = Scene()

print("Getting mesh data")
regions = scene.atlas.get_structure_descendants("root")
for reg in regions[:400]:
    try:
        scene.add_brain_region(reg)
    except FileNotFoundError:
        pass

surfaces = []
for act in scene.clean_actors:
    surfaces.append(
        (act.points(), act.faces(), np.ones(len(act.points())) * 0.5)
    )

# render stuff in napar
timer = SimpleTimer("napari")
with napari.gui_qt():
    print("creating viewer")
    viewer = napari.Viewer(ndisplay=3)

    print("Adding surfaces")
    timer.start()
    for surface in surfaces:
        try:
            viewer.add_surface(surface)
        except Exception:
            pass

    print("done")
    timer.stop()
