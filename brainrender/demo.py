"""
    A quick brainrender demo
"""
# Import the Scene class
from brainrender.scene import Scene

# Create your first scene
scene = Scene()

# Add the thalamus to your rendering
scene.add_brain_regions("TH")

# Render your scene
scene.render()
scene.close()
