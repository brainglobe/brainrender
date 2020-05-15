""" 
    This tutorial shows how to render a neuron from a .swc file
    with the MorphologyScene class
"""
from vtkplotter import Text

import brainrender
brainrender.SHADER_STYLE = 'cartoon'

from brainrender.scene import Scene

scene = Scene()

mos = scene.add_brain_regions('MOs')


a = 1