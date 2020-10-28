""" 
    This tutorial shows how to add `vedo` actors to your scene. 
"""
import brainrender

brainrender.SHADER_STYLE = "cartoon"
from brainrender.scene import Scene

# Create a scene
scene = Scene(title="Adding actors")

# There's two ways to add an actor to a scene.
# Using the '+' operator with a filepath or an instance of `vedo.Mesh`
scene + "Examples/example_files/root.obj"  # or scene += some_actor

# or using the scene class `add_actor` method
scene.add_actor(scene.root.mesh.clone().color("r"))


# You can check how many actors there are in a scene with
print(scene)  # or len(scene)

# and you can acces all actors in a scene with:
for actor in scene:
    print(f"this is an actor!: {actor}")


scene.render()
