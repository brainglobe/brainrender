from BrainRender.ABA_analyzer import ABA
from BrainRender.scene import Scene
from BrainRender.settings import *
from BrainRender.Utils.mouselight_parser import render_neurons
from BrainRender.videomaker import VideoMaker
import os



# makes scene
scene = Scene()
scene.add_brain_regions(['PAG'])
scene.Slice(axis=["z", "x"], j=[0.5, .8], onlyroot=False, )

scene.render()

# vm = VideoMaker(scene)
# vm.make_video(azimuth=2, )

