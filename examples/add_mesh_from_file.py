from brainrender import Scene

# Create a brainrender scene
scene = Scene(title="Injection in SCm")

# Add brain SCm
scene.add_brain_region("SCm")

# Add from file
scene.add("examples/data/CC_134_1_ch1inj.obj", color="tomato")

# Render!
scene.render()
