import brainrender

brainrender.WHOLE_SCREEN = True
brainrender.SHADER_STYLE = "cartoon"
from brainrender.scene import Scene


from brainrender.animation.video import BasicVideoMaker


scene = Scene(display_inset=False, camera="sagittal")

scene.add_brain_regions(["MOs"])
scene.add_neurons("Examples/example_files/neuron1.swc", color="black")

vmkr = BasicVideoMaker(scene)

vmkr.make_video(azimuth=1, niters=36, duration=30, save_name="test")
