from pathlib import Path
from rich.progress import track
import os

from ._video import Video


class VideoMaker:
    def __init__(self, scene, save_fld, name, fmt="mp4", make_frame_func=None):
        self.scene = scene

        self.save_fld = Path(save_fld)
        self.save_fld.mkdir(exist_ok=True)
        self.save_name = name
        self.video_format = fmt

        self.make_frame_func = make_frame_func or self._make_frame

    @staticmethod
    def _make_frame(scene, azimuth=0, elevation=0, roll=0):
        """
            :param azimuth: integer, specify the rotation in degrees per frame on the relative axis. (Default value = 0)
            :param elevation: integer, specify the rotation in degrees per frame on the relative axis. (Default value = 0)
            :param roll: integer, specify the rotation in degrees per frame on the relative axis. (Default value = 0)
        """
        scene.plotter.show(interactive=False)
        scene.plotter.camera.Elevation(elevation)
        scene.plotter.camera.Azimuth(azimuth)
        scene.plotter.camera.Roll(roll)

    def make_video(self, *args, duration=10, fps=30, **kwargs):
        """
        Creates a video using user defined parameters

        :param kwargs: use to change destination folder, video name, fps, duration ... check 'self.parse_kwargs' for details. 
        """
        self.scene.render(interactive=False)

        curdir = (
            os.getcwd()
        )  # we need to cd to the folder where the video is saved and then back here
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
            self.make_frame_func(self.scene, *args, **kwargs)
            video.addFrame()

        self.scene.close()
        video.close()  # merge all the recorded frames

        # Cd bacl to original dir
        os.chdir(curdir)

        return os.path.join(
            self.save_fld, self.save_name + "." + self.video_format
        )
