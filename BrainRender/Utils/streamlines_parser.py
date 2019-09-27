import sys
sys.path.append('./')

import os
import json
from vtkplotter import *

import pandas as pd
from tqdm import tqdm
import numpy as np

from BrainRender.Utils.data_io import load_json, load_neuron_swc
from BrainRender.Utils.data_manipulation import get_coords
from BrainRender.colors import *
from BrainRender.variables import *

# https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html


def parse_streamline(filepath, color='ivory', alpha=.8, radius=6):
    data = load_json(filepath)

    # create actors for streamlines
    lines = []
    for line in data['lines']:
        points = [[l['x'], l['y'], l['z']] for l in line]
        lines.append(shapes.Tube(points,  r=radius, c=color, alpha=alpha, res=NEURON_RESOLUTION))

    merged = merge(*lines)
    merged.color(color)
    return [merged]


def test():
    fld = "D:\\Dropbox (UCL - SWC)\\Rotation_vte\\analysis_metadata\\anatomy\\streamlines\\mop_wt"
    files = [os.path.join(fld, fl) for fl in os.listdir(fld)]
    
    from BrainRender.scene import Scene
    scene = Scene()
    scene.add_streamlines(files[0], color='turquoise') 
    
    scene.add_brain_regions(['MOp', 'GRN', 'MRN'], colors='ivory', alpha=.4)
    
    scene.render()

    from BrainRender.videomaker import VideoMaker

    # vm = VideoMaker(scene=scene)
    # vm.make_video(videoname="MOp_streamliens.mp4", duration=15, azimuth=3, nsteps=250)




if __name__ == "__main__":
    test()










