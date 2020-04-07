import brainrender
brainrender.WHOLE_SCREEN = True
brainrender.SHADER_STYLE = 'cartoon'
from brainrender.scene import Scene


from brainrender.animation.video import BasicVideoMaker 


scene = Scene(display_inset=False, camera="sagittal")

scene.add_brain_regions(['MOs'])
scene.add_neurons("Examples/example_files/one_neuron.json", soma_color="black")

vmkr = BasicVideoMaker(scene)

vmkr.make_video(azimuth=1, niters=360, duration=30, save_name="test")