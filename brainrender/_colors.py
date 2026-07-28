"""Color mapping and palette utilities for brainrender."""

import random

import matplotlib as mpl
import numpy as np
import numpy.typing as npt
from vedo.colors import colors as vcolors
from vedo.colors import get_color as getColor


def map_color(
    value: float,
    name: str = "jet",
    vmin: float | None = None,
    vmax: float | None = None,
) -> tuple[float, float, float]:
    """
    Map a scalar value in ``[vmin, vmax]`` to an RGB colour.

    Parameters
    ----------
    value
        Scalar value to transform into a colour.
    name
        Colormap name or matplotlib colormap. Default ``"jet"``.
    vmin
        Lower bound of the value range.
    vmax
        Upper bound of the value range.

    Returns
    -------
    tuple of float
        ``(r, g, b)`` colour.

    Raises
    ------
    ValueError
        If ``vmax`` is smaller than ``vmin``.
    """
    if vmax < vmin:
        raise ValueError("vmax should be larger than vmin")

    mp = mpl.colormaps.get_cmap(name)

    value -= vmin
    value /= vmax - vmin
    if value > 0.999:
        value = 0.999
    elif value < 0:
        value = 0
    return mp(value)[0:3]


def make_palette(N: int, *colors: str) -> list[npt.NDArray]:
    """
    Generate N colours interpolated across the given input colours.

    Adapted from vedo's ``make_palette`` function. Interpolation is
    performed in RGB space.

    Parameters
    ----------
    N
        Number of output colours.
    *colors
        Input colours. Any number between 1 and N is accepted.

    Returns
    -------
    list of numpy.ndarray
        List of ``(r, g, b)`` colour arrays.

    Raises
    ------
    ValueError
        If no colours are passed or more colours than N are passed.
    """
    N = int(N)

    N_input_colors = len(colors)
    if not N_input_colors:
        raise ValueError("No colors where passed to make_palette")
    if N_input_colors > N:
        raise ValueError(
            "More input colors than out colors (N) where passed to make_palette"
        )

    if N_input_colors == N:
        return colors
    else:
        # Get how many colors for each pair of colors we are interpolating over
        fractions = [
            N // N_input_colors + (1 if x < N % N_input_colors else 0)
            for x in range(N_input_colors)
        ]

        # Get pairs of colors
        cs = [np.array(getColor(col)) for col in colors]
        cs += [cs[-1]]

        output = []
        for n, (c1, c2) in enumerate(zip(cs, cs[1:])):
            cols = []
            for f in np.linspace(0, 1, fractions[n], endpoint=True):
                c = c1 * (1 - f) + c2 * f
                cols.append(c)
            output.extend(cols)
        return output


def get_random_colors(n_colors: int = 1) -> str | list[str]:
    """
    Return one or more random colour names from vedo's colour palette.

    Parameters
    ----------
    n_colors
        Number of colours to return. Default 1.

    Returns
    -------
    str or list of str
        A single colour name if ``n_colors == 1``, otherwise a list.
    """
    col_names = list(vcolors.keys())
    if n_colors == 1:
        return random.choice(col_names)
    else:
        return list(random.choices(col_names, k=n_colors))
