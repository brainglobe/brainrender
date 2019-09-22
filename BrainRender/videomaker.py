import os
from vtkplotter import Video
from tqdm import tqdm

from BrainRender.scene import Scene
from BrainRender.settings import *
from BrainRender.variables import *

class VideoMaker:
    def __init__(self, scene=None):
        self.scene = scene

    def add_scene(self, scene):
        self.scene = scene

    def make_video(self, *args,  videoname="video.mp4", duration=3, fps=30,
                    azimuth=0, elevation=0, roll=0,  nsteps=100,
                    save_folder = None,
                     **kwargs):
        """ [Create a video with the scene moving]

            Arguments:
                videoname {[str]} -- [name of the video to be saved. ]
                duration {[float]} -- [duration of video in seconds. ]
                fps {[float]} -- [approx framerate of output video. ]
                azimuth, elevation, roll {[int]} -- [Degrees of rotation at each step of the video. ]
                nsteps {[int]} -- [number of steps for the animation. ]
                save_folder {[str]} -- [path to folder in which to save video. If None the default "output" folder defined in settings.py will be used. ]

            ! this feature is still experimental so there might be bugs
        """

        cur_dir = os.getcwd()

        # Check save path is correct
        if save_folder is None:
            save_folder = folders_paths['output_fld']

        if not os.path.isdir(save_folder):
            raise ValueError("Save path is invalid: {}".format(save_folder))

        if "." in videoname and "mp4" not in videoname:
            raise ValueError("Only video format supported is .mp4: {}".format(videoname))
        elif "." not in videoname:
            videoname = "{}.mp4".format(videoname)

        # Change directory to target directory otherwise video doesn't get saved correctly
        os.chdir(save_folder)
        print("Saving video in: {}".format(save_folder))
        video = Video(name=videoname, duration=duration, fps=fps)

        # Make video
        self.scene.render(interactive=False, video=True)
        for i in tqdm(range(nsteps)):
            self.scene.plotter.show(offscreen=True, interactive=False)
            if azimuth:
                self.scene.plotter.camera.Azimuth(azimuth)
            if roll:
                self.scene.plotter.camera.Roll(roll)    
            if elevation:
                self.scene.plotter.camera.Elevation(elevation)

            # vp.camera.Zoom(i/40)

            video.addFrame()
        video.close()

        # Go back to original directory
        os.chdir(cur_dir)
