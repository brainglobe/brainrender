import numpy as np
import random
import vtk

# The following code and colors list is from vedo.color : https://github.com/marcomusy/vedo/blob/master/vedo/colors.py
# The code is copied here just to make it easier to look up and change colros
try:
    import matplotlib
    import matplotlib.cm as cm_mpl

    _mapscales = cm_mpl
except:
    _mapscales = None
    # see below, this is dealt with in colorMap()


#########################################################
# basic color schemes
#########################################################
# from matplotlib
colors = {
    "aliceblue": "#F0F8FF",
    "antiquewhite": "#FAEBD7",
    "aqua": "#00FFFF",
    "aquamarine": "#7FFFD4",
    "azure": "#F0FFFF",
    "beige": "#F5F5DC",
    "bisque": "#FFE4C4",
    "blanchedalmond": "#FFEBCD",
    "blue": "#0000FF",
    "blueviolet": "#8A2BE2",
    "brown": "#A52A2A",
    "burlywood": "#DEB887",
    "cadetblue": "#5F9EA0",
    "chartreuse": "#7FFF00",
    "chocolate": "#D2691E",
    "coral": "#FF7F50",
    "cornflowerblue": "#6495ED",
    "cornsilk": "#FFF8DC",
    "crimson": "#DC143C",
    "cyan": "#00FFFF",
    "darkblue": "#00008B",
    "darkcyan": "#008B8B",
    "darkgoldenrod": "#B8860B",
    "darkgray": "#A9A9A9",
    "darkgreen": "#006400",
    "darkkhaki": "#BDB76B",
    "darkmagenta": "#8B008B",
    "darkolivegreen": "#556B2F",
    "darkorange": "#FF8C00",
    "darkorchid": "#9932CC",
    "darkred": "#8B0000",
    "darksalmon": "#E9967A",
    "darkseagreen": "#8FBC8F",
    "darkslateblue": "#483D8B",
    "darkslategray": "#2F4F4F",
    "darkturquoise": "#00CED1",
    "darkviolet": "#9400D3",
    "deeppink": "#FF1493",
    "deepskyblue": "#00BFFF",
    "dimgray": "#696969",
    "dodgerblue": "#1E90FF",
    "firebrick": "#B22222",
    "floralwhite": "#FFFAF0",
    "forestgreen": "#228B22",
    "fuchsia": "#FF00FF",
    "gainsboro": "#DCDCDC",
    "ghostwhite": "#F8F8FF",
    "gold": "#FFD700",
    "goldenrod": "#DAA520",
    "gray": "#808080",
    "green": "#008000",
    "greenyellow": "#ADFF2F",
    "honeydew": "#F0FFF0",
    "hotpink": "#FF69B4",
    "indianred": "#CD5C5C",
    "indigo": "#4B0082",
    "ivory": "#FFFFF0",
    "khaki": "#F0E68C",
    "lavender": "#E6E6FA",
    "lavenderblush": "#FFF0F5",
    "lawngreen": "#7CFC00",
    "lemonchiffon": "#FFFACD",
    "lightblue": "#ADD8E6",
    "lightcoral": "#F08080",
    "lightcyan": "#E0FFFF",
    "lightgray": "#D3D3D3",
    "lightgreen": "#90EE90",
    "lightpink": "#FFB6C1",
    "lightsalmon": "#FFA07A",
    "lightseagreen": "#20B2AA",
    "lightskyblue": "#87CEFA",
    "lightsteelblue": "#B0C4DE",
    "lightyellow": "#FFFFE0",
    "lime": "#00FF00",
    "limegreen": "#32CD32",
    "linen": "#FAF0E6",
    "magenta": "#FF00FF",
    "maroon": "#800000",
    "mediumaquamarine": "#66CDAA",
    "mediumblue": "#0000CD",
    "mediumorchid": "#BA55D3",
    "mediumpurple": "#9370DB",
    "mediumseagreen": "#3CB371",
    "mediumslateblue": "#7B68EE",
    "mediumspringgreen": "#00FA9A",
    "mediumturquoise": "#48D1CC",
    "mediumvioletred": "#C71585",
    "midnightblue": "#191970",
    "mintcream": "#F5FFFA",
    "mistyrose": "#FFE4E1",
    "moccasin": "#FFE4B5",
    "navajowhite": "#FFDEAD",
    "navy": "#000080",
    "oldlace": "#FDF5E6",
    "olive": "#808000",
    "olivedrab": "#6B8E23",
    "orange": "#FFA500",
    "orangered": "#FF4500",
    "orchid": "#DA70D6",
    "palegoldenrod": "#EEE8AA",
    "palegreen": "#98FB98",
    "paleturquoise": "#AFEEEE",
    "palevioletred": "#DB7093",
    "papayawhip": "#FFEFD5",
    "peachpuff": "#FFDAB9",
    "peru": "#CD853F",
    "pink": "#FFC0CB",
    "plum": "#DDA0DD",
    "powderblue": "#B0E0E6",
    "purple": "#800080",
    "rebeccapurple": "#663399",
    "red": "#FF0000",
    "rosybrown": "#BC8F8F",
    "royalblue": "#4169E1",
    "saddlebrown": "#8B4513",
    "salmon": "#FA8072",
    "sandybrown": "#F4A460",
    "seagreen": "#2E8B57",
    "seashell": "#FFF5EE",
    "sienna": "#A0522D",
    "silver": "#C0C0C0",
    "skyblue": "#87CEEB",
    "slateblue": "#6A5ACD",
    "slategray": "#708090",
    "snow": "#FFFAFA",
    "blackboard": "#393939",
    "springgreen": "#00FF7F",
    "steelblue": "#4682B4",
    "tan": "#D2B48C",
    "teal": "#008080",
    "thistle": "#D8BFD8",
    "tomato": "#FF6347",
    "turquoise": "#40E0D0",
    "violet": "#EE82EE",
    "wheat": "#F5DEB3",
    "white": "#FFFFFF",
    "whitesmoke": "#F5F5F5",
    "yellow": "#FFFF00",
    "yellowgreen": "#9ACD32",
}

# color nicknames
color_nicks = {
    "a": "aqua",
    "b": "blue",
    "bb": "blackboard",
    "c": "cyan",
    "f": "fuchsia",
    "g": "green",
    "i": "indigo",
    "m": "magenta",
    "n": "navy",
    "l": "lavender",
    "o": "orange",
    "p": "purple",
    "r": "red",
    "s": "salmon",
    "t": "tomato",
    "v": "violet",
    "y": "yellow",
    "w": "white",
    "lb": "lightblue",  # light
    "lg": "lightgreen",
    "lr": "orangered",
    "lc": "lightcyan",
    "ls": "lightsalmon",
    "ly": "lightyellow",
    "dr": "darkred",  # dark
    "db": "darkblue",
    "dg": "darkgreen",
    "dm": "darkmagenta",
    "dc": "darkcyan",
    "ds": "darksalmon",
    "dv": "darkviolet",
}

# available colormap names from matplotlib:
_mapscales_cmaps = (
    "Accent",
    "Accent_r",
    "Blues",
    "Blues_r",
    "BrBG",
    "BrBG_r",
    "BuGn",
    "BuGn_r",
    "BuPu",
    "BuPu_r",
    "CMRmap",
    "CMRmap_r",
    "Dark2",
    "Dark2_r",
    "GnBu",
    "GnBu_r",
    "Greens",
    "Greens_r",
    "Greys",
    "Greys_r",
    "OrRd",
    "OrRd_r",
    "Oranges",
    "Oranges_r",
    "PRGn",
    "PRGn_r",
    "Paired",
    "Paired_r",
    "Pastel1",
    "Pastel1_r",
    "Pastel2",
    "Pastel2_r",
    "PiYG",
    "PiYG_r",
    "PuBu",
    "PuBuGn",
    "PuBuGn_r",
    "PuBu_r",
    "PuOr",
    "PuOr_r",
    "PuRd",
    "PuRd_r",
    "Purples",
    "Purples_r",
    "RdBu",
    "RdBu_r",
    "RdGy",
    "RdGy_r",
    "RdPu",
    "RdPu_r",
    "RdYlBu",
    "RdYlBu_r",
    "RdYlGn",
    "RdYlGn_r",
    "Reds",
    "Reds_r",
    "Set1",
    "Set1_r",
    "Set2",
    "Set2_r",
    "Set3",
    "Set3_r",
    "Spectral",
    "Spectral_r",
    "Wistia",
    "Wistia_r",
    "YlGn",
    "YlGnBu",
    "YlGnBu_r",
    "YlGn_r",
    "YlOrBr",
    "YlOrBr_r",
    "YlOrRd",
    "YlOrRd_r",
    "afmhot",
    "afmhot_r",
    "autumn",
    "autumn_r",
    "binary",
    "binary_r",
    "bone",
    "bone_r",
    "brg",
    "brg_r",
    "bwr",
    "bwr_r",
    "cividis",
    "cividis_r",
    "cool",
    "cool_r",
    "coolwarm",
    "coolwarm_r",
    "copper",
    "copper_r",
    "cubehelix",
    "cubehelix_r",
    "flag",
    "flag_r",
    "gist_earth",
    "gist_earth_r",
    "gist_gray",
    "gist_gray_r",
    "gist_heat",
    "gist_heat_r",
    "gist_ncar",
    "gist_ncar_r",
    "gist_rainbow",
    "gist_rainbow_r",
    "gist_stern",
    "gist_stern_r",
    "gist_yarg",
    "gist_yarg_r",
    "gnuplot",
    "gnuplot2",
    "gnuplot2_r",
    "gnuplot_r",
    "gray_r",
    "hot",
    "hot_r",
    "hsv",
    "hsv_r",
    "inferno",
    "inferno_r",
    "jet",
    "jet_r",
    "magma",
    "magma_r",
    "nipy_spectral",
    "nipy_spectral_r",
    "ocean",
    "ocean_r",
    "pink_r",
    "plasma",
    "plasma_r",
    "prism",
    "prism_r",
    "rainbow",
    "rainbow_r",
    "seismic",
    "seismic_r",
    "spring",
    "spring_r",
    "summer",
    "summer_r",
    "tab10",
    "tab10_r",
    "tab20",
    "tab20_r",
    "tab20b",
    "tab20b_r",
    "tab20c",
    "tab20c_r",
    "terrain",
    "terrain_r",
    "twilight",
    "twilight_r",
    "twilight_shifted",
    "twilight_shifted_r",
    "viridis",
    "viridis_r",
    "winter",
    "winter_r",
)

# default sets of colors
colors1 = [
    [1.0, 0.832, 0.000],  # gold
    [0.960, 0.509, 0.188],
    [0.901, 0.098, 0.194],
    [0.235, 0.85, 0.294],
    [0.46, 0.48, 0.000],
    [0.274, 0.941, 0.941],
    [0.0, 0.509, 0.784],
    [0.1, 0.1, 0.900],
    [0.902, 0.7, 1.000],
    [0.941, 0.196, 0.901],
]
# negative integer color number get this:
colors2 = [
    (0.99, 0.83, 0),  # gold
    (0.59, 0.0, 0.09),  # dark red
    (0.5, 1.0, 0.0),  # green
    (0.5, 0.5, 0),  # yellow-green
    (0.0, 0.66, 0.42),  # green blue
    (0.0, 0.18, 0.65),  # blue
    (0.4, 0.0, 0.4),  # plum
    (0.4, 0.0, 0.6),
    (0.2, 0.4, 0.6),
    (0.1, 0.3, 0.2),
]


def get_random_colormap():
    return random.choice(_mapscales_cmaps)


def get_n_shades_of(shade, n):
    """
    :param shade:  color
    :param n: numnber of colors

    """
    shades = [k for k, v in colors.items() if shade in k]
    if not shades:
        raise ValueError("Could not find shades for {}".format(shade))
    else:
        return random.choices(shades, k=n)


def _isSequence(arg):
    """

    :param arg:   item to check

    """
    # Check if input is iterable.
    if hasattr(arg, "strip"):
        return False
    if hasattr(arg, "__getslice__"):
        return True
    if hasattr(arg, "__iter__"):
        return True
    return False


def getColor(rgb=None, hsv=None):
    """Convert a color or list of colors to (r,g,b) format from many different input formats.

    :param bool: hsv: if set to `True`, rgb is assumed as (hue, saturation, value).
    Example:
         - RGB    = (255, 255, 255), corresponds to white
         - rgb    = (1,1,1) is white
         - hex    = #FFFF00 is yellow
         - string = 'white'
         - string = 'w' is white nickname
         - string = 'dr' is darkred
         - int    =  7 picks color nr. 7 in a predefined color list
         - int    = -7 picks color nr. 7 in a different predefined list
    |colorcubes| |colorcubes.py|_
    :param rgb:  (Default value = None)
    :param hsv:  (Default value = None)

    """
    # recursion, return a list if input is list of colors:
    if _isSequence(rgb) and (len(rgb) > 3 or _isSequence(rgb[0])):
        seqcol = []
        for sc in rgb:
            seqcol.append(getColor(sc))
        return seqcol

    if str(rgb).isdigit():
        rgb = int(rgb)

    if hsv:
        c = hsv2rgb(hsv)
    else:
        c = rgb

    if _isSequence(c):
        if c[0] <= 1 and c[1] <= 1 and c[2] <= 1:
            return c  # already rgb
        else:
            if len(c) == 3:
                return list(np.array(c) / 255.0)  # RGB
            else:
                return (c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, c[3])  # RGBA

    elif isinstance(c, str):  # is string
        c = c.replace("grey", "gray").replace(" ", "")
        if 0 < len(c) < 3:  # single/double letter color
            if c.lower() in color_nicks.keys():
                c = color_nicks[c.lower()]
            else:
                print("Unknow color nickname:", c)
                print("Available abbreviations:", color_nicks)
                return (0.5, 0.5, 0.5)

        if c.lower() in colors.keys():  # matplotlib name color
            c = colors[c.lower()]
        else:  # vtk name color
            namedColors = vtk.vtkNamedColors()
            rgba = [0, 0, 0, 0]
            namedColors.GetColor(c, rgba)
            return list(np.array(rgba[0:3]) / 255.0)

        if "#" in c:  # hex to rgb
            h = c.lstrip("#")
            rgb255 = list(int(h[i : i + 2], 16) for i in (0, 2, 4))
            rgbh = np.array(rgb255) / 255.0
            if np.sum(rgbh) > 3:
                print("Error in getColor(): Wrong hex color", c)
                return (0.5, 0.5, 0.5)
            return tuple(rgbh)

    elif isinstance(c, int):  # color number
        if c >= 0:
            return colors1[c % 10]
        else:
            return colors2[-c % 10]

    elif isinstance(c, float):
        if c >= 0:
            return colors1[int(c) % 10]
        else:
            return colors2[int(-c) % 10]

    # print("Unknown color:", c)
    return (0.5, 0.5, 0.5)


def getColorName(c):
    """Find the name of a color.
    |colorpalette| |colorpalette.py|_

    :param c: c 

    """
    c = np.array(getColor(c))  # reformat to rgb
    mdist = 99.0
    kclosest = ""
    for key in colors.keys():
        ci = np.array(getColor(key))
        d = np.linalg.norm(c - ci)
        if d < mdist:
            mdist = d
            kclosest = str(key)
    return kclosest


def hsv2rgb(hsv):
    """Convert HSV to RGB color.

    :param hsv: gsv 

    """
    ma = vtk.vtkMath()
    return ma.HSVToRGB(hsv)


def rgb2hsv(rgb):
    """Convert RGB to HSV color.

    :param rgb: rgb 

    """
    ma = vtk.vtkMath()
    return ma.RGBToHSV(getColor(rgb))


def rgb2int(rgb_tuple):
    """

    :param rgb_tuple: rgb 

    """
    rgb = (
        int(rgb_tuple[0] * 255),
        int(rgb_tuple[1] * 255),
        int(rgb_tuple[2] * 255),
    )
    return 65536 * rgb[0] + 256 * rgb[1] + rgb[2]


def colorMap(value, name="jet", vmin=None, vmax=None):
    """Map a real value in range [vmin, vmax] to a (r,g,b) color scale.

    :param value: scalar value to transform into a color
    :type value: float, list
    :param name: color map name (Default value = "jet")
    :type name: str, matplotlib.colors.LinearSegmentedColormap
    :param vmin:  (Default value = None)
    :param vmax:  (Default value = None)
    :returns: return: (r,g,b) color, or a list of (r,g,b) colors.
    .. note:: Most frequently used color maps:
        |colormaps|
        Matplotlib full list:
        .. image:: https://matplotlib.org/1.2.1/_images/show_colormaps.png
    .. tip:: Can also use directly a matplotlib color map:
        :Example:
            .. code-block:: python
                from vedo import colorMap
                import matplotlib.cm as cm
                print( colorMap(0.2, cm.flag, 0, 1) )
                (1.0, 0.809016994374948, 0.6173258487801733)

    """
    if not _mapscales:
        print(
            "-------------------------------------------------------------------"
        )
        print(
            "WARNING : cannot import matplotlib.cm (colormaps will show up gray)."
        )
        print("Try e.g.: sudo apt-get install python3-matplotlib")
        print("     or : pip install matplotlib")
        print(
            "     or : build your own map (see example in basic/mesh_custom.py)."
        )
        return (0.5, 0.5, 0.5)

    if isinstance(name, matplotlib.colors.LinearSegmentedColormap):
        mp = name
    else:
        mp = cm_mpl.get_cmap(name=name)

    if _isSequence(value):
        values = np.array(value)
        if vmin is None:
            vmin = np.min(values)
        if vmax is None:
            vmax = np.max(values)
        values = np.clip(values, vmin, vmax)
        values -= vmin
        values = values / (vmax - vmin)
        cols = []
        mp = cm_mpl.get_cmap(name=name)
        for v in values:
            cols.append(mp(v)[0:3])
        return np.array(cols)
    else:
        value -= vmin
        value /= vmax - vmin
        if value > 0.999:
            value = 0.999
        elif value < 0:
            value = 0
        return mp(value)[0:3]


def makePalette(N, *colors):
    """Generate N colors starting from `color1` to `color2`
    by linear interpolation HSV in or RGB spaces.
    Adapted from vedo makePalette function

    :param int: N: number of output colors.
    :param colors: input colors, any number of colors with 0 < ncolors <= N is okay.
    """
    if not isinstance(N, (float, int)):
        raise ValueError(
            f"The first argument N should be an integer, not {type(N)}."
        )
    N = int(N)

    N_input_colors = len(colors)
    if not N_input_colors:
        raise ValueError("No colors where passed to makePalette")
    if N_input_colors > N:
        raise ValueError(
            "More input colors than out colors (N) where passed to makePalette"
        )

    if N_input_colors == 1:
        return [np.array(getColor(colors[0])) for n in np.arange(N)]
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

        if len(output) != N:
            if len(output) > N:
                return output[:N]
            else:
                raise ValueError(
                    f"Expected number of output colors was {N} but we got {len(output)} instead"
                )
        return output


def get_random_colors(n_colors=1):
    """

    :param n_colors:  (Default value = 1)

    """
    if not isinstance(n_colors, np.int):
        raise ValueError("n_colors should be an integer")
    if n_colors <= 0:
        raise ValueError("n_colors should be bigger or equal to 0")

    if n_colors == 1:
        return random.choice(list(colors.keys()))
    else:
        return list(random.choices(list(colors.keys()), k=n_colors))


def check_colors(color):
    """

    :param color: color 

    """
    if isinstance(color, list):
        for col in color:
            try:
                getColor(col)
            except:
                return False
    else:
        try:
            getColor(color)
        except:
            return False
    return True
