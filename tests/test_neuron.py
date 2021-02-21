from brainrender import Scene
from brainrender.actors import Neuron, make_neurons
from brainrender.actor import Actor
from vedo import Sphere
import pytest


def test_neuron():

    s = Scene(title="BR")

    neuron = s.add(Neuron("tests/files/neuron1.swc"))
    s.add(Neuron(Actor(neuron.mesh)))
    s.add(Neuron(neuron.mesh))
    Neuron(Sphere())

    with pytest.raises(ValueError):
        Neuron(1)

    with pytest.raises(FileExistsError):
        Neuron("tests/files/neuronsfsfs.swc")
    with pytest.raises(NotImplementedError):
        Neuron("tests/files/random_cells.h5")

    del s


def test_make_neurons():
    make_neurons("tests/files/neuron1.swc", "tests/files/neuron1.swc")
