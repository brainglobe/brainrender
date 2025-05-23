from pathlib import Path

from loguru import logger
from morphapi.morphology.morphology import Neuron as MorphoNeuron
from pyinspect.utils import _class_name
from vedo import Mesh

from brainrender.actor import Actor


def make_neurons(
    *neurons, alpha=1, color=None, neurite_radius=8, soma_radius=15, name=None
):
    """
    Returns a list of Neurons given a variable number of inputs
    :param neurons: any accepted data input for Neuron
    :param alpha: float
    :param color: str
    :param neurite_radius: float, radius of axon/dendrites
    :param soma_radius: float, radius of soma
    :param name: str, actor name
    """
    return [
        Neuron(
            n,
            alpha=alpha,
            color=color,
            neurite_radius=neurite_radius,
            soma_radius=soma_radius,
            name=name,
        )
        for n in neurons
    ]


class Neuron(Actor):
    def __init__(
        self,
        neuron,
        color=None,
        alpha=1,
        neurite_radius=8,
        soma_radius=15,
        invert_dims=True,
        name=None,
    ):
        """
        Creates an Actor representing a single neuron's morphology
        :param neuron: path to .swc file, Mesh, Actor or Neuron from morphapi.morphology
        :param alpha: float
        :param color: str,
        :param neuron_radius: float, radius of axon/dendrites
        :param soma_radius: float, radius of soma
        :param invert_dims: bool, exchange the first and last dimension coordinates
        when loading from a .swc file. e.g going from (x, y, z) to (z, y, x).
        :param name: str, actor name
        """
        logger.debug("Creating a Neuron actor")
        if color is None:
            color = "blackboard"
        alpha = alpha
        self.neurite_radius = neurite_radius
        self.soma_radius = soma_radius
        self.name = None

        if isinstance(neuron, (str, Path)):
            mesh = self._from_file(neuron, invert_dims)
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

    def _from_morphapi_neuron(self, neuron: MorphoNeuron):
        # Temporarily set cache to false as meshes were being corrupted
        # on second load
        mesh = neuron.create_mesh(
            neurite_radius=self.neurite_radius,
            soma_radius=self.soma_radius,
            use_cache=False,
        )[1]
        return mesh

    def _from_file(self, neuron: (str, Path), invert_dims):
        path = Path(neuron)
        if not path.exists():
            raise FileExistsError(f"Neuron file doesn't exist: {path}")

        if not path.suffix == ".swc":
            raise NotImplementedError(
                "Neuron can load morphology only from brainrender.swc files"
            )

        self.name = self.name or path.name

        return self._from_morphapi_neuron(
            MorphoNeuron(data_file=neuron, invert_dims=invert_dims)
        )
