import sys
sys.path.append('./')

import os
from vtkplotter import shapes, merge

import pandas as pd
from tqdm import tqdm
import numpy as np

from brainrender.Utils.data_io import load_json
from brainrender import STREAMLINES_RESOLUTION, INJECTION_VOLUME_SIZE
from brainrender.Utils.webqueries import request

def parse_streamline(*args, filepath=None, data=None, show_injection_site=True, color='ivory', alpha=.8, radius=10, **kwargs):
    """
        Given a path to a .json file with streamline data (or the data themselves), render the streamline as tubes actors.
        Either  filepath or data should be passed

        :param filepath: str, optional. Path to .json file with streamline data (Default value = None)
        :param data: panadas.DataFrame, optional. DataFrame with streamline data. (Default value = None)
        :param color: str color of the streamlines (Default value = 'ivory')
        :param alpha: float transparency of the streamlines (Default value = .8)
        :param radius: int radius of the streamlines actor (Default value = 10)
        :param show_injection_site: bool, if True spheres are used to render the injection volume (Default value = True)
        :param *args: 
        :param **kwargs: 

    """
    if filepath is not None and data is None:
        data = load_json(filepath)
        # data = {k:{int(k2):v2 for k2, v2 in v.items()} for k,v in data.items()}
    elif filepath is None and data is not None:
        pass
    else:
        raise ValueError("Need to pass eiteher a filepath or data argument to parse_streamline")

    # create actors for streamlines
    lines = []
    if len(data['lines']) == 1:
        lines_data = data['lines'][0]
    else:
        lines_data = data['lines']
    for line in lines_data:
        points = [[l['x'], l['y'], l['z']] for l in line]
        lines.append(shapes.Tube(points,  r=radius, c=color, alpha=alpha, res=STREAMLINES_RESOLUTION))

    coords = []
    if show_injection_site:
        if len(data['injection_sites']) == 1:
            injection_data = data['injection_sites'][0]
        else:
            injection_data = data['injection_sites']

        for inj in injection_data:
            coords.append(list(inj.values()))
        spheres = [shapes.Spheres(coords, r=INJECTION_VOLUME_SIZE)]
    else:
        spheres = []

    merged = merge(*lines, *spheres)
    merged.color(color)
    merged.alpha(alpha)
    return [merged]










