try:
    import cv2
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "You need opencv to save videos in brainrender, please install opencv with: "
        + "pip install opencv-python"
    )


from vedo import Video as VtkVideo
import datetime
import os

from brainrender.Utils.video import save_videocap_to_video


class Video(VtkVideo):
    # Redifine vedo.Video close method
    def __init__(self, *args, fmt="mp4", **kwargs):
        super().__init__(*args, **kwargs)
        self.format = fmt

    def get_cap_from_images_folder(self, img_format="%1d.png"):
        """
            It creates a cv2 VideoCaptur 'cap' from a folder of images (frames)
        """
        if not os.path.isdir(self.tmp_dir.name):
            raise ValueError(f"Folder {self.tmp_dir.name} doesn't exist")
        if not os.listdir(self.tmp_dir.name):
            raise ValueError(f"Folder {self.tmp_dir.name} is empty")

        # Create video capture
        cap = cv2.VideoCapture(os.path.join(self.tmp_dir.name, img_format))

        # Check all went well
        ret, frame = cap.read()
        if not ret:
            raise ValueError(
                "Something went wrong, can't read form folder: "
                + self.tmp_dir.name
            )
        else:
            cap.set(1, 0)  # reset cap to first frame
        return cap

    def close(self):
        """
            Takes a folder full of frames saved as images and converts it into a video.
        """
        # Save frames as video
        cap = self.get_cap_from_images_folder()
        save_videocap_to_video(
            cap,
            self.name + "." + self.format,
            self.format,
            int(self.fps),
            iscolor=True,
        )
        print(f"Saved video as: {self.name}.{self.format}")

        # Clean up
        self.tmp_dir.cleanup()


class BasicVideoMaker:
    """
        Wrapper around vedo Video class to facilitate the creation of videos from
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
        self.save_fld = kwargs.pop("save_fld", self.scene.atlas.output_videos)
        self.save_name = kwargs.pop(
            "save_name",
            "brainrender_video_"
            + f'_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}',
        )
        self.video_format = kwargs.pop("video_format", "mp4")

        self.duration = kwargs.pop("duration", 3)
        self.niters = kwargs.pop("niters", 60)
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
        self.save_fld = kwargs.pop("save_fld", self.save_fld)
        self.save_name = kwargs.pop("save_name", self.save_name)
        self.video_format = kwargs.pop("video_format", self.video_format)
        self.duration = kwargs.pop("duration", None)
        self.niters = kwargs.pop("niters", self.niters)
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

        curdir = (
            os.getcwd()
        )  # we need to cd to the folder where the video is saved and then back here
        os.chdir(self.save_fld)
        print(f"Saving video in {self.save_fld}")

        # Create video
        video = Video(
            name=self.save_name,
            duration=self.duration,
            fps=self.fps,
            fmt=self.video_format,
        )

        # Render the scene first
        self.scene.render(interactive=False)

        # Make frames
        for i in range(self.niters):
            self.scene.plotter.show()  # render(interactive=False, video=True)  # render the scene first
            self.scene.plotter.camera.Elevation(elevation)
            self.scene.plotter.camera.Azimuth(azimuth)
            self.scene.plotter.camera.Roll(roll)
            video.addFrame()

        self.scene.close()
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
            - have a 'videomaker' keyword argument to accept the CustomVideoMaker (self) instance
            - have a 'video' keyword that takes the Video argument
            - return the instance of Video

        The custom function can manipulate actors and camera in the scene and 
        add frames to the video with 'video.addFrame()'. 
        Once all frames are ready it has to return the video object 
        so that the video can be closed and saved.     

        :param video_function: custom function used to generate the video's frames

        see: examples/advanced/custom_videomaker.py

        """
        self.parse_kwargs(**kwargs)
        os.chdir(self.save_fld)

        # Create video
        video = Video(
            name=self.save_name, duration=self.duration, fps=self.fps
        )

        # run custom function
        video = video_function(scene=self.scene, video=video, videomaker=self)

        # Check output
        if video is None or not isinstance(video, Video):
            raise ValueError(
                "The custom video function didn't return anything "
                + "or it returned something other than the instance of Video "
                + "It must return the video object so that it can be closed properly."
            )
        if not isinstance(video, Video):
            raise ValueError(
                f"The custom video function returned invalid objects: {video} instead of video object"
            )

        # close video
        video.close()
