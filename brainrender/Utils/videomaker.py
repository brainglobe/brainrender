import sys
sys.path.append("./")

from vtkplotter import Video
import os

class VideoMaker:
    def __init__(self, scene, **kwargs):
        """
        This class takes care of creating videos with animating scenes.
        """
        self.scene = scene

        self.savename = kwargs.pop("savename", None)
        self.savefile = kwargs.pop("savefile", None) # path of the video to be saved
        self.duration = kwargs.pop("duration", None)
        self.niters = kwargs.pop("niters", None)
        self.fps = kwargs.pop("fps", None)

        self.default_savefile = ""
        self.default_duration = 5
        self.default_fps = 30
        self.default_niters = 50

    def update_params(self, **kwargs):
        """

        :param **kwargs: 

        """
        self.savefile = kwargs.pop("savefile", self.savefile)
        self.duration = kwargs.pop("duration", self.duration)
        self.niters = kwargs.pop("niters", self.niters)
        self.fps = kwargs.pop("fps", self.fps)

    def _setup_videos(self):
        """
        Checks that variables useful for creating a video (e.g. fps) have been set, sets them as default parameters otherwise.
        """
        # check if scene is rendered
        if not self.scene.is_rendered:
            self.scene.render(interactive=False, video=True)
        else:
            pass
            # ! not sure what happens if you call this after having already rendered the scene

        # check if we have params set by users
        _vars = {'savefile':self.savefile, 'fps':self.fps, 'duration':self.duration, 'niters':self.niters}
        defaults = [self.default_savefile, self.default_fps, self.default_duration, self.default_niters]
        names = ["save file", "fps", "duration", "number of iterations"]
        for (varname, var), name, default in zip(_vars.items(), names, defaults):
            if var is None:
                print("No {} was passed, using default: {}".format(name, default))
                self.__setattr__(varname, default)

        # check that the save file path makes sense
        if not ".mp4" in self.savefile:
            if not "." in self.savefile:
                self.savefile+".mp4"
            else:
                raise NotImplementedError("Video Maker only supports saving to .mp4 because vtkplotter only supports .mp4, sorry.")


    def make_video(self, azimuth=0, elevation=0, roll=0):
        """
        Creates a video using user defined parameters
    
        :param azimuth: integer, specify the rotation in degrees per frame on the relative axis. (Default value = 0)
        :param elevation: integer, specify the rotation in degrees per frame on the relative axis. (Default value = 0)
        :param roll: integer, specify the rotation in degrees per frame on the relative axis. (Default value = 0)

        """
        self._setup_videos()

        # open a video file and force it to last 3 seconds in total
        # folder = os.path.dirname(self.savefile)
        # name = os.path.basename(self.savefile)
        # curdir = os.getcwd()
        # os.chdir(folder)
        video = Video(name=self.savefile, duration=self.duration, fps=self.fps)

        for i in range(self.niters):
            self.scene.plotter.show()  # render the scene first
            self.scene.plotter.camera.Elevation(elevation)
            self.scene.plotter.camera.Azimuth(azimuth)
            self.scene.plotter.camera.Roll(roll) 
            video.addFrame()
        video.close()  # merge all the recorded frames
        os.chdir(curdir)

    def make_video_custom(self, videofunc):
        """
        Let's users use a custom function to create the video. This function can do any manipulation of
        video frames it wants, but it MUST have 'scene' and 'video' keyword arguments. The function must also return video object.

        :param videofunc: function
        """
        self._setup_videos()

        # open a video file and force it to last 3 seconds in total
        video = Video(name=self.savefile, duration=self.duration, fps=self.fps)

        # run custom function
        video = videofunc(scene=self, video=video)

        if video is None: raise ValueError("The custom video function didn't return anything. It must return the video object so that it can be closed properly.")

        # close video
        video.close()  
