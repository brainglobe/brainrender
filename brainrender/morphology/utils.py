from brainrender import DEFAULT_NEURITE_RADIUS, SOMA_RADIUS
from morphapi.morphology.morphology import Neuron
from vedo import merge


def get_neuron_actors_with_morphapi(
    swcfile=None,
    neuron=None,
    neurite_radius=None,
    use_cache=True,
    soma_radius=None,
):
    if swcfile is None and neuron is None:
        raise ValueError("No input passed")

    if swcfile is not None:
        neuron = Neuron(swc_file=swcfile)

    if neurite_radius is None:
        neurite_radius = DEFAULT_NEURITE_RADIUS
    if soma_radius is None:
        soma_radius = SOMA_RADIUS

    actors = neuron.create_mesh(
        neurite_radius=neurite_radius,
        use_cache=use_cache,
        soma_radius=soma_radius,
    )
    if actors is None:
        raise ValueError(f"Failed to get neuron actors. {swcfile} - {neuron}")
    else:
        neurites, whole_neuron = actors

    actors = dict(
        soma=neurites["soma"],
        axon=neurites["axon"],
        dendrites=merge(
            neurites["basal_dendrites"], neurites["apical_dendrites"]
        ),
    )

    return actors, whole_neuron
