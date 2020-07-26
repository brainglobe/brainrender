from brainrender.scene import Scene

# brainrender.SCREENSHOT_TRANSPARENT_BACKGROUND = False

scene = Scene()

scene.add_brain_regions(["CA1"])

scene.add_optic_cannula(target_region="CA1")

p0 = scene.atlas.get_region_CenterOfMass("MOs")
scene.add_optic_cannula(pos=p0)

scene.render()
