from brainrender import Scene

# Create a brainrender scene using the zebrafish atlas
scene = Scene(atlas_name="mpin_zfish_1um", title="zebrafish")

# Render!
scene.render()
