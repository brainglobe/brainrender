import os
import numpy as np

from vedo import merge
from vedo.mesh import Mesh as Actor
from vedo import settings

from morphapi.morphology.morphology import Neuron

import brainrender
from brainrender.scene import Scene
from brainrender.colors import colorMap, getColor, _mapscales_cmaps
from brainrender.morphology.utils import get_neuron_actors_with_morphapi
from brainrender.Utils.data_manipulation import return_list_smart


class MorphologyScene(Scene):

    _default_axes_params = dict(
        xyGrid=True,
        yzGrid=True,
        zxGrid=True,
        xyPlaneColor="k",
        zxPlaneColor=[0.2, 0.2, 0.2],
        yzPlaneColor=[0.2, 0.2, 0.2],
        # xyGridColor = 'red',
        # xyAlpha = 1,
        # # axesLineWidth = 10,
        gridLineWidth=0,
        xyGridColor="k",
        zxGridColor="k",
        yzGridColor="k",
    )

    def __init__(self, *args, **kwargs):
        self.default_neuron_color = kwargs.pop(
            "default_neuron_color", "darksalmon"
        )
        show_axes = kwargs.pop("show_axes", True)
        axes_kwargs = kwargs.pop("axes_kwargs", 1)
        settings.DEFAULT_NEURITE_RADIUS = ("neurite_radius", 18)

        if axes_kwargs == 1:
            settings.useDepthPeeling = (
                False  # necessary to make the axes render properly
            )
            settings.useFXAA = False

        # Initialise scene class
        Scene.__init__(
            self, add_root=False, display_inset=False, *args, **kwargs
        )

        if show_axes:
            brainrender.SHOW_AXES = True
            if axes_kwargs == 1:
                self.plotter.axes = self._default_axes_params

            else:
                self.plotter.axes = axes_kwargs

    def _add_neurons_get_colors(self, neurons, color):
        """     
            Parses color argument for self.add_neurons
            
            :para, neurons: list of Neuron object or file paths...
            :param color: default None. Can be:
                - None: each neuron is colored according to the default color
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
            cols = [self.default_neuron_color for n in np.arange(N)]
            colors = dict(
                soma=cols.copy(), axon=cols.copy(), dendrites=cols.copy(),
            )
        else:
            if isinstance(color, str):
                # Deal with a a cmap being passed
                if color in _mapscales_cmaps:
                    cols = [
                        colorMap(n, name=color, vmin=-2, vmax=N + 2)
                        for n in np.arange(N)
                    ]
                    colors = dict(
                        soma=cols.copy(),
                        axon=cols.copy(),
                        dendrites=cols.copy(),
                    )

                else:
                    # Deal with a single color being passed
                    cols = [getColor(color) for n in np.arange(N)]
                    colors = dict(
                        soma=cols.copy(),
                        axon=cols.copy(),
                        dendrites=cols.copy(),
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
                        dendrites_colors.append(
                            col.pop("dendrites", col["soma"])
                        )
                        axon_colors.append(col.pop("axon", col["soma"]))
                        soma_colors.append(col["soma"])

                    colors = dict(
                        soma=soma_colors,
                        axon=axon_colors,
                        dendrites=dendrites_colors,
                    )

                else:
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

    def add_neurons(
        self,
        neurons,
        color=None,
        display_axon=True,
        display_dendrites=True,
        alpha=1,
        neurite_radius=None,
    ):
        """
            Adds rendered morphological data of neurons reconstructions downloaded from the
            Mouse Light project at Janelia, neuromorpho.org and other sources. 
            Accepts neurons argument as:
                - file(s) with morphological data
                - vedo mesh actor(s) of neurons reconstructions
                - dictionary or list of dictionary with actors for different neuron parts

            :param self: instance of brainrender Scene to use to render neurons
            :param neurons: str, list, dict. File(s) with neurons data or list of rendered neurons.
            :param display_axon, display_dendrites: if set to False the corresponding neurite is not rendered
            :param color: default None. Can be:
                    - None: each neuron is colored according to the default color
                    - color: rbg, hex etc. If a single color is passed all neurons will have that color
                    - cmap: str with name of a colormap: neurons are colored based on their sequential order and cmap
                    - dict: a dictionary specifying a color for soma, dendrites and axon actors, will be the same for all neurons
                    - list: a list of length = number of neurons with either a single color for each neuron
                            or a dictionary of colors for each neuron
            :param alpha: float in range 0,1. Neurons transparency
            :param neurite_radius: float > 0 , radius of tube actor representing neurites
        """

        if not isinstance(neurons, (list, tuple)):
            neurons = [neurons]

        # ------------------------------ Prepare colors ------------------------------ #
        colors = self._add_neurons_get_colors(neurons, color)

        # ---------------------------------- Render ---------------------------------- #
        _neurons_actors = []
        for neuron in neurons:
            neuron_actors = {"soma": None, "dendrites": None, "axon": None}

            # Deal with neuron as filepath
            if isinstance(neuron, str):
                if os.path.isfile(neuron):
                    if neuron.endswith(".swc"):
                        neuron_actors, _ = get_neuron_actors_with_morphapi(
                            swcfile=neuron, neurite_radius=neurite_radius
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
            elif isinstance(neuron, Actor):
                # A single actor was passed, maybe it's the entire neuron
                neuron_actors["soma"] = neuron  # store it as soma anyway
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
                            neuron["apical_dendrites"],
                            neuron["basal_dendrites"],
                        )
                else:
                    neuron_actors["dendrites"] = neuron.pop("dendrites", None)

            # Deal with neuron as instance of Neuron from morphapi
            elif isinstance(neuron, Neuron):
                neuron_actors, _ = get_neuron_actors_with_morphapi(
                    neuron=neuron
                )
            # Deal with other inputs
            else:
                raise ValueError(
                    f"Passed neuron {neuron} is not a valid input"
                )

            # Check that we don't have anything weird in neuron_actors
            for key, act in neuron_actors.items():
                if act is not None:
                    if not isinstance(act, Actor):
                        raise ValueError(
                            f"Neuron actor {key} is {act.__type__} but should be a vedo Mesh. Not: {act}"
                        )

            if not display_axon:
                neuron_actors["axon"] = None
            if not display_dendrites:
                neuron_actors["dendrites"] = None
            _neurons_actors.append(neuron_actors)

        # Color actors
        for n, neuron in enumerate(_neurons_actors):
            if neuron["axon"] is not None:
                neuron["axon"].c(colors["axon"][n])
            neuron["soma"].c(colors["soma"][n])
            if neuron["dendrites"] is not None:
                neuron["dendrites"].c(colors["dendrites"][n])

        # Add to actors storage
        self.actors.extend([list(n.values()) for n in _neurons_actors])

        return return_list_smart(_neurons_actors)
