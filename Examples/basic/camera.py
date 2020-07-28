""" 
    This tutorial shows how to create regions with specific camera parameters
"""
import brainrender

brainrender.SHADER_STYLE = "cartoon"
from brainrender.scene import Scene

# Create a scene
scene = Scene(
    camera="top", title="camera"
)  # specify that you want a view from the top

# render
scene.render()

# Now render but with a different view
scene.render(camera="sagittal", zoom=1, title="camera")

# Now render but with specific camera parameters
bespoke_camera = dict(
    position=[801.843, -1339.564, 8120.729],
    focal=[9207.34, 2416.64, 5689.725],
    viewup=[0.36, -0.917, -0.171],
    distance=9522.144,
    clipping=[5892.778, 14113.736],
)

scene.render(camera=bespoke_camera)
