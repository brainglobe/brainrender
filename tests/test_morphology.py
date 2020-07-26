import pytest
import brainrender

brainrender.SHADER_STYLE = "cartoon"
from brainrender.morphology.visualise import MorphologyScene


@pytest.fixture
def scene():
    return MorphologyScene(title="A neuron")


def test_color_options(scene):
    scene.add_neurons(
        "Examples/example_files/neuron4.swc",
        color=dict(soma="red", dendrites="orangered", axon=[0.4, 0.4, 0.4],),
    )

    scene.add_neurons(
        "Examples/example_files/neuron4.swc",
        color=[dict(soma="red", dendrites="orangered", axon=[0.4, 0.4, 0.4],)],
    )

    scene.add_neurons("Examples/example_files/neuron4.swc",)

    scene.add_neurons("Examples/example_files/neuron4.swc", color="salmon")

    scene.add_neurons("Examples/example_files/neuron4.swc", color="Reds")

    scene.add_neurons("Examples/example_files/neuron4.swc", color=["seagreen"])


def test_render_options(scene):
    scene.add_neurons(
        "Examples/example_files/neuron4.swc", neurite_radius=None,
    )

    scene.add_neurons(
        ["Examples/example_files/neuron4.swc"], neurite_radius=None,
    )

    scene.add_neurons(
        "Examples/example_files/neuron4.swc", neurite_radius=None,
    )

    scene.add_neurons(
        "Examples/example_files/neuron4.swc",
        display_axon=False,
        neurite_radius=None,
    )

    scene.add_neurons(
        "Examples/example_files/neuron4.swc",
        display_dendrites=False,
        neurite_radius=None,
    )

    scene.add_neurons(
        "Examples/example_files/neuron4.swc",
        display_axon=False,
        display_dendrites=False,
        neurite_radius=None,
    )
