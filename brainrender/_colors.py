import numpy as np
from vedo.colors import getColor
from vedo.colors import colors as vcolors
import random
import matplotlib.cm as cm_mpl


def map_color(value, name="jet", vmin=None, vmax=None):
    """Map a real value in range [vmin, vmax] to a (r,g,b) color scale.

    :param value: scalar value to transform into a color
    :type value: float, list
    :param name: color map name (Default value = "jet")
    :type name: str, matplotlib.colors.LinearSegmentedColorMap
    :param vmin:  (Default value = None)
    :param vmax:  (Default value = None)
    :returns: return: (r,g,b) color, or a list of (r,g,b) colors.
    """
    if vmax < vmin:
        raise ValueError("vmax should be larger than vmin")

    mp = cm_mpl.get_cmap(name=name)

    value -= vmin
    value /= vmax - vmin
    if value > 0.999:
        value = 0.999
    elif value < 0:
        value = 0
    return mp(value)[0:3]


def make_palette(N, *colors):
    """Generate N colors starting from `color1` to `color2`
    by linear interpolation HSV in or RGB spaces.
    Adapted from vedo make_palette function

    :param int: N: number of output colors.
    :param colors: input colors, any number of colors with 0 < ncolors <= N is okay.
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


def get_random_colors(n_colors=1):
    """
    :param n_colors:  (Default value = 1)
    """
    col_names = list(vcolors.keys())
    if n_colors == 1:
        return random.choice(col_names)
    else:
        return list(random.choices(col_names, k=n_colors))
