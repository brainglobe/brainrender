from brainrender import Scene

# Create a brainrender scene
scene = Scene(title="brain regions")

# Add brain regions
scene.add_brain_region("TH")

# You can specify color, transparency...
scene.add_brain_region("MOs", "CA1", alpha=0.2, color="green")

# Render!
scene.render()
