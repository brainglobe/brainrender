"""
    This example shows how to add a 3d object to the scene by loading
    it from file and moving/scaling it to be aligned correctly.
    In this case the object is a .stl file of the mouse skull, 
    but it could be anything, including experimental and recording devices.

    Note that the mouse skull and brain meshes come from different sources
    so that's why they don't match perfectly.
"""


import brainrender

brainrender.SHADER_STYLE = "cartoon"
brainrender.ROOT_ALPHA = 1

from brainrender.scene import Scene

scene = Scene()

# Load skull from file
skull = scene.add_from_file("Examples/example_files/skull.stl")
skull.mesh.c("ivory").alpha(1)

# Align skull and brain (scene.root)
skull_com = skull.mesh.centerOfMass()
root_com = scene.root.mesh.centerOfMass()

skull.mesh.origin(skull.mesh.centerOfMass())
skull.mesh.rotateY(90).rotateX(180)
skull.mesh.x(root_com[0] - skull_com[0])
skull.mesh.y(root_com[1] - skull_com[1])
skull.mesh.z(root_com[2] - skull_com[2])
skull.mesh.x(3500)
skull.mesh.rotateZ(-25)
skull.mesh.y(7800)
skull.mesh.scale([1300, 1500, 1200])


# Cut skull actor to show brain inside
scene.cut_actors_with_plane("sagittal", actors=skull)

# Improve looks
scene.add_silhouette(scene.root, skull, lw=3)

scene.render()
