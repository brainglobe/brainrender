"""
    This example shows you how to crate a multi scene
    visualisation in brainrender
"""

from brainrender.scene import MultiScene, Scene

# Create 3 scenes
scene1 = Scene()
scene1.add_brain_regions("MOs")

scene2 = Scene(add_root=False)
scene2.add_brain_regions(["TH", "VAL"])

scene3 = Scene()
scene3.add_brain_regions("CA1")


# Create and render a multiscene
multi = MultiScene(3, scenes=[scene1, scene2, scene3])
multi.render()
