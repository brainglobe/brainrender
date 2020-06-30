"""
    A quick brainrender demo
"""

from brainrender.scene import Scene

scene = Scene()
scene.add_brain_regions("TH")

scene.render()
scene.close()
