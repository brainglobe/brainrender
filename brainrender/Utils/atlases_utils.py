import numpy as np
from vedo import Mesh, merge
from morphapi.morphology.morphology import Neuron
import os

from brainrender.Utils.data_manipulation import return_list_smart
from brainrender.morphology.utils import get_neuron_actors_with_morphapi
from brainrender.colors import (
    getColor,
    colorMap,
    _mapscales_cmaps,
    get_random_colors,
)


def parse_neurons_colors(neurons, color):
    """
        Prepares the color info to render neurons

        :param neurons: str, list, dict. File(s) with neurons data or list of rendered neurons.
        :param color: default None. Can be:
                - None: each neuron is given a random color
                - color: rbg, hex etc. If a single color is passed all neurons will have that color
                - cmap: str with name of a colormap: neurons are colored based on their sequential order and cmap
                - dict: a dictionary specifying a color for soma, dendrites and axon actors, will be the same for all neurons
                - list: a list of length = number of neurons with either a single color for each neuron
                        or a dictionary of colors for each neuron
    """

    N = len(neurons)
    colors = dict(soma=None, axon=None, dendrites=None,)

    # If no color is passed, get random colors
    if color is None:
        cols = get_random_colors(N)
        if not isinstance(cols, list):
            cols = [cols]
        colors = dict(soma=cols, axon=cols, dendrites=cols,)
    else:
        if isinstance(color, str):
            # Deal with a a cmap being passed
            if color in _mapscales_cmaps:
                cols = [
                    colorMap(n, name=color, vmin=-2, vmax=N + 2)
                    for n in np.arange(N)
                ]
                colors = dict(
                    soma=cols.copy(), axon=cols.copy(), dendrites=cols.copy(),
                )

            else:
                # Deal with a single color being passed
                cols = [getColor(color) for n in np.arange(N)]
                colors = dict(
                    soma=cols.copy(), axon=cols.copy(), dendrites=cols.copy(),
                )
        elif isinstance(color, dict):
            # Deal with a dictionary with color for each component
            if "soma" not in color.keys():
                raise ValueError(
                    f"When passing a dictionary as color argument, \
                                            soma should be one fo the keys: {color}"
                )
            dendrites_color = color.pop("dendrites", color["soma"])
            axon_color = color.pop("axon", color["soma"])

            colors = dict(
                soma=[color["soma"] for n in np.arange(N)],
                axon=[axon_color for n in np.arange(N)],
                dendrites=[dendrites_color for n in np.arange(N)],
            )

        elif isinstance(color, (list, tuple)):
            # Check that the list content makes sense
            if len(color) != N:
                raise ValueError(
                    "When passing a list of color arguments, the list length"
                    + f" ({len(color)}) should match the number of neurons ({N})."
                )
            if len(set([type(c) for c in color])) > 1:
                raise ValueError(
                    "When passing a list of color arguments, all list elements"
                    + " should have the same type (e.g. str or dict)"
                )

            if isinstance(color[0], dict):
                # Deal with a list of dictionaries
                soma_colors, dendrites_colors, axon_colors = [], [], []

                for col in color:
                    if "soma" not in col.keys():
                        raise ValueError(
                            f"When passing a dictionary as col argument, \
                                                    soma should be one fo the keys: {col}"
                        )
                    dendrites_colors.append(col.pop("dendrites", col["soma"]))
                    axon_colors.append(col.pop("axon", col["soma"]))
                    soma_colors.append(col["soma"])

                colors = dict(
                    soma=soma_colors,
                    axon=axon_colors,
                    dendrites=dendrites_colors,
                )

            else:
                if isinstance(color, tuple):
                    color = [color]
                # Deal with a list of colors
                colors = dict(
                    soma=color.copy(),
                    axon=color.copy(),
                    dendrites=color.copy(),
                )
        else:
            raise ValueError(
                f"Color argument passed is not valid. Should be a \
                                    str, dict, list or None, not {type(color)}:{color}"
            )

    # Check colors, if everything went well we should have N colors per entry
    for k, v in colors.items():
        if len(v) != N:
            raise ValueError(
                f"Something went wrong while preparing colors. Not all \
                            entries have right length. We got: {colors}"
            )

    return colors


def get_neurons(
    neurons,
    color=None,
    display_axon=True,
    display_dendrites=True,
    alpha=1,
    neurite_radius=None,
    soma_radius=None,
    use_cache=True,
):
    """
    Gets rendered morphological data of neurons reconstructions
    Accepts neurons argument as:
        - file(s) with morphological data
        - vedo mesh actor(s) of entire neurons reconstructions
        - dictionary or list of dictionary with actors for different neuron parts

    :param neurons: str, list, dict. File(s) with neurons data or list of rendered neurons.
    :param display_axon, display_dendrites: if set to False the corresponding neurite is not rendered
    :param color: default None. Can be:
            - None: each neuron is given a random color
            - color: rbg, hex etc. If a single color is passed all neurons will have that color
            - cmap: str with name of a colormap: neurons are colored based on their sequential order and cmap
            - dict: a dictionary specifying a color for soma, dendrites and axon actors, will be the same for all neurons
            - list: a list of length = number of neurons with either a single color for each neuron
                    or a dictionary of colors for each neuron
    :param alpha: float in range 0,1. Neurons transparency
    :param neurite_radius: float > 0 , radius of tube actor representing neurites
    :param use_cache: bool, if True a cache is used to avoid having to crate a neuron's mesh anew, otherwise a new mesh is created
    """

    if not isinstance(neurons, (list, tuple)):
        neurons = [neurons]

    # ---------------------------------- Render ---------------------------------- #
    _neurons_actors = []
    for neuron in neurons:
        neuron_actors = {"soma": None, "dendrites": None, "axon": None}

        # Deal with neuron as filepath
        if isinstance(neuron, str):
            if os.path.isfile(neuron):
                if neuron.endswith(".swc"):
                    neuron_actors, _ = get_neuron_actors_with_morphapi(
                        swcfile=neuron,
                        neurite_radius=neurite_radius,
                        soma_radius=soma_radius,
                        use_cache=use_cache,
                    )
                else:
                    raise NotImplementedError(
                        "Currently we can only parse morphological reconstructions from swc files"
                    )
            else:
                raise ValueError(
                    f"Passed neruon {neuron} is not a valid input. Maybe the file doesn't exist?"
                )

        # Deal with neuron as single actor
        elif isinstance(neuron, Mesh):
            # A single actor was passed, maybe it's the entire neuron
            neuron_actors["soma"] = neuron  # store it as soma
            pass

        # Deal with neuron as dictionary of actor
        elif isinstance(neuron, dict):
            neuron_actors["soma"] = neuron.pop("soma", None)
            neuron_actors["axon"] = neuron.pop("axon", None)

            # Get dendrites actors
            if (
                "apical_dendrites" in neuron.keys()
                or "basal_dendrites" in neuron.keys()
            ):
                if "apical_dendrites" not in neuron.keys():
                    neuron_actors["dendrites"] = neuron["basal_dendrites"]
                elif "basal_dendrites" not in neuron.keys():
                    neuron_actors["dendrites"] = neuron["apical_dendrites"]
                else:
                    neuron_actors["dendrites"] = merge(
                        neuron["apical_dendrites"], neuron["basal_dendrites"],
                    )
            else:
                neuron_actors["dendrites"] = neuron.pop("dendrites", None)

        # Deal with neuron as instance of Neuron from morphapi
        elif isinstance(neuron, Neuron):
            neuron_actors, _ = get_neuron_actors_with_morphapi(
                neuron=neuron,
                neurite_radius=neurite_radius,
                use_cache=use_cache,
            )
        # Deal with other inputs
        else:
            raise ValueError(f"Passed neuron {neuron} is not a valid input")

        # Check that we don't have anything weird in neuron_actors
        for key, act in neuron_actors.items():
            if act is not None:
                if not isinstance(act, Mesh):
                    raise ValueError(
                        f"Neuron actor {key} is {type(act)} but should be a vedo Mesh. Not: {act}"
                    )

        if not display_axon:
            neuron_actors["axon"] = None
        if not display_dendrites:
            neuron_actors["dendrites"] = None
        _neurons_actors.append(neuron_actors)

    # Color actors
    colors = parse_neurons_colors(neurons, color)
    for n, neuron in enumerate(_neurons_actors):
        if neuron["axon"] is not None:
            neuron["axon"].c(colors["axon"][n])
            neuron["axon"].name = "neuron-axon"
        if neuron["soma"] is not None:
            neuron["soma"].c(colors["soma"][n])
            neuron["soma"].name = "neuron-soma"
        if neuron["dendrites"] is not None:
            neuron["dendrites"].c(colors["dendrites"][n])
            neuron["dendrites"].name = "neuron-dendrites"

    # Return
    return return_list_smart(_neurons_actors), None
