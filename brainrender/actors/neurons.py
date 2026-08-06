"""Neuron morphology actors for brainrender scenes."""

from pathlib import Path

from loguru import logger
from morphapi.morphology.morphology import Neuron as MorphoNeuron
from pyinspect.utils import _class_name
from vedo import Mesh

from brainrender.actor import Actor


def make_neurons(
    *neurons: str | Path | Mesh | Actor | MorphoNeuron,
    alpha: float = 1,
    color: str | None = None,
    neurite_radius: float = 8,
    soma_radius: float = 15,
    name: str | None = None,
) -> list["Neuron"]:
    """
    Create Neuron actors from one or more inputs.

    Parameters
    ----------
    *neurons
        Any accepted input for Neuron.
    alpha
        Transparency. Default 1.
    color
        Colour name. Default ``"blackboard"``.
    neurite_radius
        Radius of axon/dendrites. Default 8.
    soma_radius
        Radius of soma. Default 15.
    name
        Actor name.

    Returns
    -------
    list of Neuron
        A list of Neuron actors, one for each input.
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
    """Actor representing a single neuron's morphology."""

    def __init__(
        self,
        neuron: str | Path | Mesh | Actor | MorphoNeuron,
        color: str | None = None,
        alpha: float = 1,
        neurite_radius: float = 8,
        soma_radius: float = 15,
        invert_dims: bool = True,
        name: str | None = None,
    ) -> None:
        """
        Parameters
        ----------
        neuron
            Path to a ``.swc`` file, a Mesh, an Actor, or a
            morphapi Neuron instance.
        color
            Colour name. Default ``"blackboard"``.
        alpha
            Transparency. Default 1.
        neurite_radius
            Radius of axon/dendrites. Default 8.
        soma_radius
            Radius of soma. Default 15.
        invert_dims
            If True, swap the first and last coordinate dimensions when
            loading from a ``.swc`` file (e.g. ``(x, y, z)`` → ``(z, y, x)``).
        name
            Actor name.

        Raises
        ------
        ValueError
            If ``neuron`` is not a recognised input type.
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

    def _from_morphapi_neuron(self, neuron: MorphoNeuron) -> Mesh:
        """
        Create a mesh from a morphapi Neuron instance.

        Parameters
        ----------
        neuron
            morphapi Neuron instance.

        Returns
        -------
        vedo.Mesh
            A mesh created from the morphapi Neuron instance.
        """
        # Temporarily set cache to false as meshes were being corrupted
        # on second load
        mesh = neuron.create_mesh(
            neurite_radius=self.neurite_radius,
            soma_radius=self.soma_radius,
            use_cache=False,
        )[1]
        return mesh

    def _from_file(
        self,
        neuron: str | Path,
        invert_dims: bool,
    ) -> Mesh:
        """
        Load neuron morphology from a ``.swc`` file.

        Parameters
        ----------
        neuron
            Path to the ``.swc`` file.
        invert_dims
            If True, swap the first and last coordinate dimensions.

        Returns
        -------
        vedo.Mesh

        Raises
        ------
        FileExistsError
            If the file does not exist.
        NotImplementedError
            If the file is not a ``.swc`` file.
        """
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
