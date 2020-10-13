from brainrender.scene import Scene
from morphapi.api.mpin_celldb import MpinMorphologyAPI


def test_fish_neurons():
    api = MpinMorphologyAPI()
    # api.download_dataset()
    neurons_ids = api.get_neurons_by_structure(837)[:5]
    neurons = api.load_neurons(neurons_ids)

    neurons = [
        neuron.create_mesh(soma_radius=1, neurite_radius=1)[1]
        for neuron in neurons
    ]

    scene = Scene(atlas="mpin_zfish_1um", add_root=True, camera="sagittal2")
    scene.add_neurons(neurons)
    scene.render(interactive=False)
    scene.close()
