"""
    This example shows you how to crate a multi scene
    visualisation in brainrender
"""

from brainrender.scene import MultiScene, Scene

# Create 3 scenes
scene1 = Scene()
scene1.add_brain_region("MOs")

scene2 = Scene(add_root=False)
scene2.add_brain_region(["TH", "VAL"])

scene3 = Scene()
scene3.add_brain_region("CA1")


# Create and render a multiscene
multi = MultiScene(3, scenes=[scene1, scene2, scene3])
multi.render()
