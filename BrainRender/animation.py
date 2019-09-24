import os
from vtkplotter import *
from tqdm import tqdm

from BrainRender.scene import Scene
from BrainRender.settings import *
from BrainRender.variables import *


class Animator:
    def __init__(self, scene=None):
        self.scene = scene
        # if scene is not None:
        #     self.scene.render(interactive=False, video=True)


    def add_scene(self, scene):
        self.scene = scene
        # self.scene.render(interactive=False, video=True)


    def test(self):
        # vp = Animation()
        # vp.showProgressBar = True
        # vp.timeResolution = 0.025  # secs

        # actors = list(self.scene.actors["regions"].values())
        # all_actors = self.scene.get_actors()

        # vp.fadeIn(all_actors, t=0, duration=1)
        # vp.fadeOut(actors, t=1, duration=1)
        # vp.fadeIn(actors, t=2, duration=1)

        # # all_actors = self.scene.get_actors()
        # # vp.scale(all_actors, 2, t=5, duration=1)
        # # vp.rotate(all_actors, axis="y", angle=180)

        # vp.totalDuration = 4 # can shrink/expand total duration
        # vp.play()

        sp = Sphere(r=0.5).cutWithPlane(origin=(0.15,0,0)).lw(0.1)
        cu = Cube().pos(-2,0,0)
        tr = Torus().pos(1,0,0).rotateY(80)

        vp = Animation()
        vp.showProgressBar = True
        vp.timeResolution = 0.025  # secs

        vp.fadeIn([cu, tr], t=0, duration=0.2)
        vp.fadeIn(sp, t=1, duration=2)

        vp.move(sp, (2,0,0), style="linear")
        vp.rotate(sp, axis="y", angle=180)

        vp.fadeOut(sp, t=3, duration=2)
        vp.fadeOut(tr, t=4, duration=1)

        vp.scale(cu, 0.1, t=5, duration=1)

        vp.totalDuration = 4 # can shrink/expand total duration

        vp.play()
