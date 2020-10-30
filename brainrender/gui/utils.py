import numpy as np


def get_region_actors(actors, region):
    acts = [act for act in actors if act.name == region]

    if acts:
        return acts[0]
    else:
        return None


def get_color_from_string(string):
    try:
        rgb = string.replace("[", "").replace("]", "")
        color = np.array([float(c) for c in rgb.split(" ")])
        return color
    except ValueError:
        return string.lower()


def get_alpha_from_string(string):
    try:
        return float(string)
    except ValueError:
        return None
