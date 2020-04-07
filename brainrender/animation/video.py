from vtkplotter import Video
import datetime
import os


class BasicVideoMaker:
    """
        Wrapper around vtkplotter Video class to facilitate the creation of videos from
        brainrender scenes.

        Use kwargs to specify:
            - save_fld: folder where to save video
            - save_name: video name
            - video_format: e.g. mp4
            - duration: video duration in seconds
            - niters: number of iterations (frames) when creating the video
            - fps: framerate of video
    """
    def __init__(self, scene, **kwargs):
        self.scene = scene
        
        # Parss keyword argumets
        self.save_fld = kwargs.pop('save_fld', self.scene.output_videos)
        self.save_name = kwargs.pop('save_name', 'brainrender_video_'+
                            f'_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}')
        self.video_format = kwargs.pop('video_format', 'mp4')

        self.duration = kwargs.pop('duration', 3)
        self.niters = kwargs.pop('niters', 60)
        self.fps = kwargs.pop("fps", 30)

    def parse_kwargs(self, **kwargs):
        """
            Parses arguments for video creation
            Use kwargs to specify:
                - save_fld: folder where to save video
                - save_name: video name
                - video_format: e.g. mp4
                - duration: video duration in seconds
                - niters: number of iterations (frames) when creating the video
                - fps: framerate of video

            Arguments not specified in kwargs will be assigned default values
        """
        self.save_fld = kwargs.pop('save_fld', self.save_fld)
        self.save_name = kwargs.pop('save_name', self.save_name)
        self.video_format = kwargs.pop('video_format', self.video_format)
        self.duration = kwargs.pop('duration', None)
        self.niters = kwargs.pop('niters', self.niters)
        self.fps = kwargs.pop("fps", self.fps)

    def make_video(self, azimuth=0, elevation=0, roll=0, **kwargs):
        """
        Creates a video using user defined parameters

        :param azimuth: integer, specify the rotation in degrees per frame on the relative axis. (Default value = 0)
        :param elevation: integer, specify the rotation in degrees per frame on the relative axis. (Default value = 0)
        :param roll: integer, specify the rotation in degrees per frame on the relative axis. (Default value = 0)
        :param kwargs: use to change destination folder, video name, fps, duration ... check 'self.parse_kwargs' for details. 
        """
        self.parse_kwargs(**kwargs)

        curdir = os.getcwd() # we need to cd to the folder where the video is saved and then back here
        os.chdir(self.save_fld)
        print(f"Saving video in {self.save_fld}")

        # Create video
        video = Video(name=self.save_name, 
                    duration=self.duration, fps=self.fps)

        # Render the scene first
        self.scene.render(interactive=False)

        # Make frames
        for i in range(self.niters):
            self.scene.plotter.show() # render(interactive=False, video=True)  # render the scene first
            self.scene.plotter.camera.Elevation(elevation)
            self.scene.plotter.camera.Azimuth(azimuth)
            self.scene.plotter.camera.Roll(roll) 
            video.addFrame()
        video.close()  # merge all the recorded frames

        # Cd bake to original dir
        os.chdir(curdir)

class CustomVideoMaker(BasicVideoMaker):
    """
        Subclasses BasicVideoMaker and replaces make_video method.
    """
    def __init__(self, scene, **kwargs):
        BasicVideoMaker.__init__(self, scene, **kwargs)

    def make_video(self, video_function, **kwargs):
        """
        Let's users use a custom function to create the video.
        The custom function must:
            - have a 'scene' keyword argument to accept a Scene() instance
            - have a 'video' keyword argument to accept a Video() instance
            - return the instance of Video

        The custom function can manipulate actors and camera in the scene and 
        add frames to the video with 'video.addFrame()'. 
        Once all frames are ready it has to return the video object 
        so that the video can be closed and saved.     

        """
        self.parse_kwargs(**kwargs)

        curdir = os.getcwd() # we need to cd to the folder where the video is saved and then back here
        os.chdir(self.save_fld)

        # Create video
        video = Video(name=self.save_name+self.video_format, 
                    duration=self.duration, fps=self.fps)

        # run custom function
        video = videofunc(scene=self.scene, video=video)

        # Check output
        if video is None: 
            raise ValueError("The custom video function didn't return anything."+
                                    "It must return the video object so that it can be closed properly.")
        if not isinstance(video, Video):
            raise ValueError(f"The custom video function returned invalid objects: {video} instead of video object")

        # close video
        video.close()  