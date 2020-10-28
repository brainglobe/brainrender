from pathlib import Path
from morphapi.morphology.morphology import Neuron as MorphoNeuron
from vedo import Mesh
from pyinspect.utils import _class_name

from ..actor import Actor


def get_neurons(*neurons):
    return [Neuron(n) for n in neurons]


class Neuron(Actor):
    def __init__(
        self,
        neuron,
        color=None,
        alpha=1,
        neurite_radius=8,
        soma_radius=15,
        name=None,
    ):
        """
            neuron can be either a .swc, a Mesh, or a morphapi.Neuron
        """
        color = color or "blackboard"
        alpha = alpha
        self.neurite_radius = neurite_radius
        self.soma_radius = soma_radius
        self.name = None

        if isinstance(neuron, (str, Path)):
            mesh = self._from_file(neuron)
        elif isinstance(neuron, (Mesh)):
            mesh = neuron
        elif isinstance(neuron, Actor):
            mesh = neuron.mesh
        elif isinstance(neuron, MorphoNeuron):
            mesh = self._from_morphapi_neuron(neuron)
        else:
            raise ValueError(
                f'Argument "neuron" is not in a recognized format: {_class_name(neuron)}'
            )

        Actor.__init__(self, mesh, name=self.name, br_class="Neuron")
        self.mesh.c(color).alpha(alpha)

    def _from_morphapi_neuron(self, neuron):
        mesh = neuron.create_mesh(
            neurite_radius=self.neurite_radius, soma_radius=self.soma_radius
        )[1]
        return mesh

    def _from_file(self, neuron):
        path = Path(neuron)
        if not path.exists():
            raise FileExistsError(f"Neuron file doesnt exist: {path}")

        if not path.suffix == ".swc":
            raise NotImplementedError(
                "Neuron can load morphology only from .swc files"
            )

        self.name = self.name or path.name
        return self._from_morphapi_neuron(MorphoNeuron(data_file=neuron))
