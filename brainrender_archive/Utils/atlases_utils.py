import numpy as np
from accepts import accepts
from brainrender.colors import (
    getColor,
    colorMap,
    _mapscales_cmaps,
    get_random_colors,
)


@accepts((str, list, dict), (type(None), str, list, np.ndarray, dict, tuple))
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
