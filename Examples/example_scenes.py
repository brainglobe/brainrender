import sys
sys.path.append("./")
from BrainRender.scene import Scene
from BrainRender.variables import *
from BrainRender.Utils.ABA.connectome import ABA


scene = Scene()
regions = ["MOs", "VISp", "ZI"]

scene.add_brain_regions(regions, use_original_color=True)

scene.render()