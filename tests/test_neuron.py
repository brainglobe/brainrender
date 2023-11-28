from importlib.resources import files

import pytest
from vedo import Sphere

from brainrender import Scene
from brainrender.actor import Actor
from brainrender.actors import Neuron, make_neurons


def test_neuron():
    s = Scene(title="BR")
    neuron = s.add(
        Neuron(files("brainrender").joinpath("resources/neuron1.swc"))
    )
    s.add(Neuron(Actor(neuron.mesh)))
    s.add(Neuron(neuron.mesh))
    Neuron(Sphere())

    with pytest.raises(ValueError):
        Neuron(1)

    with pytest.raises(FileExistsError):
        Neuron(files("brainrender").joinpath("resources/neuronsfsfs.swc"))
    with pytest.raises(NotImplementedError):
        Neuron(files("brainrender").joinpath("resources/random_cells.h5"))

    del s


def test_make_neurons():
    data_path = files("brainrender").joinpath("resources/neuron1.swc")
    make_neurons(data_path, data_path)
