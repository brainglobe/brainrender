import brainrender
brainrender.SHADER_STYLE = 'cartoon'

from brainrender.scene import Scene

sharptrack_file = 'Examples/example_files/sharptrack_probe_points.mat'

scene = Scene(use_default_key_bindings=True)

scene.add_brain_regions('TH', alpha=.2, wireframe=True)

scene.add_probe_from_sharptrack(sharptrack_file)

scene.render()