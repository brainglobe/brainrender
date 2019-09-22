from BrainRender.ABA_analyzer import ABA
from BrainRender.scene import Scene
from BrainRender.settings import *
from BrainRender.Utils.mouselight_parser import render_neurons
import os

from vtkplotter import settings

useParallelProjection = True
useFXAA = True
useDepthPeeling  = True


# get vars to populate test scene
br = ABA()

# makes scene
scene = Scene()
scene.add_brain_regions(['PAG'])
scene.render()

