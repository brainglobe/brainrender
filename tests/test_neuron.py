from pathlib import Path

import pytest
from vedo import Sphere

from brainrender import Scene
from brainrender.actor import Actor
from brainrender.actors import Neuron, make_neurons

resources_dir = Path(__file__).parent.parent / "resources"


def test_neuron():
    s = Scene(title="BR")
    neuron = s.add(Neuron(resources_dir / "neuron1.swc"))
    s.add(Neuron(Actor(neuron.mesh)))
    s.add(Neuron(neuron.mesh))
    Neuron(Sphere())

    with pytest.raises(ValueError):
        Neuron(1)

    with pytest.raises(FileExistsError):
        Neuron(resources_dir / "neuronsfsfs.swc")
    with pytest.raises(NotImplementedError):
        Neuron(resources_dir / "random_cells.h5")

    del s


def test_make_neurons():
    data_path = resources_dir / "neuron1.swc"
    make_neurons(data_path, data_path)
