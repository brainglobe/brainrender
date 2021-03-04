from benchmark.timer import Timer
from brainrender import Scene


scene = Scene(inset=False)
regions = scene.atlas.get_structure_descendants("root")

with Timer(scene, name="Brain regions"):
    for reg in regions:
        try:
            scene.add_brain_region(reg)
        except FileNotFoundError:
            pass


scene.close()
