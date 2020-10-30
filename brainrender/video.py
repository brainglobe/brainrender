from pathlib import Path
from rich.progress import track
import os

from ._video import Video


class VideoMaker:
    def __init__(self, scene, save_fld, name, fmt="mp4", make_frame_func=None):
        """
            Creates a video by animating a scene and saving a sequence
            of screenshots.

            :param scene: the instance of Scene to be animated
            :param save_fld: str, Path. Where the video will be savd
            :param save_name: str, name of the video
            :param fmt: str. Video format (e.g. 'mp4')
            :param make_frame_func: None, optional. If passed it should be a
                function that takes the Scene to be animated as the fist argument abd
                the current frame number as second. At every frame this function
                can do what's needed to animate the scne
        """
        self.scene = scene

        self.save_fld = Path(save_fld)
        self.save_fld.mkdir(exist_ok=True)
        self.save_name = name
        self.video_format = fmt

        self.make_frame_func = make_frame_func or self._make_frame

    @staticmethod
    def _make_frame(scene, frame_number, azimuth=0, elevation=0, roll=0):
        """
            Default `make_frame_func`. Rotaets the camera in 3 directions

            :param scene: scene to be animated.
            :param frame_number: int, not used
            :param azimuth: integer, specify the rotation in degrees 
                        per frame on the relative axis. (Default value = 0)
            :param elevation: integer, specify the rotation in degrees 
                        per frame on the relative axis. (Default value = 0)
            :param roll: integer, specify the rotation in degrees 
                        per frame on the relative axis. (Default value = 0)
        """
        scene.plotter.show(interactive=False)
        scene.plotter.camera.Elevation(elevation)
        scene.plotter.camera.Azimuth(azimuth)
        scene.plotter.camera.Roll(roll)

    def make_video(
        self, *args, duration=10, fps=30, render_kwargs={}, **kwargs
    ):
        """
        Creates a video using user defined parameters

        :param *args: any extra argument to be bassed to `make_frame_func`
        :param duration: float, duratino of the video in seconds
        :param fps: int, frame rate
        :param **kwargs: any extra keyword argument to be bassed to `make_frame_func`
        """
        self.scene.render(interactive=False, **render_kwargs)

        # cd to folder where the video will be saved
        curdir = os.getcwd()
        os.chdir(self.save_fld)
        print(f"Saving video in {self.save_fld}")

        # Create video
        video = Video(
            name=self.save_name,
            duration=duration,
            fps=fps,
            fmt=self.video_format,
        )

        # Make frames
        niters = int(fps * duration)
        for i in track(range(niters)):
            self.make_frame_func(self.scene, i, *args, **kwargs)
            video.addFrame()

        self.scene.close()
        video.close()  # merge all the recorded frames

        # Cd back to original dir
        os.chdir(curdir)

        return os.path.join(
            self.save_fld, self.save_name + "." + self.video_format
        )
