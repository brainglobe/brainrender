import brainrender
brainrender.WHOLE_SCREEN = True
brainrender.SHADER_STYLE = 'cartoon'
from brainrender.scene import Scene


from brainrender.animation.video import BasicVideoMaker 


scene = Scene(display_inset=False)

scene.add_brain_regions(['MOs'])
scene.add_neurons("Examples\example_files\one_neuron.json")

vmkr = BasicVideoMaker(scene)

vmkr.make_video(azimuth=3.6, niters=10, save_name="test")