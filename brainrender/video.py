from pathlib import Path
from rich.progress import track
from rich import print
from pyinspect._colors import orange
import os
import numpy as np

from .camera import check_camera_param
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
    def _make_frame(
        scene, frame_number, tot_frames, azimuth=0, elevation=0, roll=0
    ):
        """
            Default `make_frame_func`. Rotaets the camera in 3 directions

            :param scene: scene to be animated.
            :param frame_number: int, not used
            :param tot_frames: int, total numner of frames
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

    def generate_frames(self, fps, duration, video, *args, **kwargs):
        """
            Loop to generate frames
        """
        nframes = int(fps * duration)
        for i in track(range(nframes)):
            self.make_frame_func(self.scene, i, nframes, *args, **kwargs)
            video.addFrame()

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
        self.generate_frames(fps, duration, video, *args, **kwargs)

        self.scene.close()
        video.close()  # merge all the recorded frames

        # Cd back to original dir
        os.chdir(curdir)

        return os.path.join(
            self.save_fld, self.save_name + "." + self.video_format
        )


class Animation(VideoMaker):
    _last_frame_params = None

    def __init__(self, scene, save_fld, name, fmt="mp4", make_frame_func=None):
        VideoMaker.__init__(self, scene, save_fld, name, fmt=fmt)

        self.keyframes = {}
        self.keyframes[0] = dict(  # make sure first frame is a keyframe
            zoom=None, camera=None, callback=None
        )

    def add_keyframe(
        self, frame_number, zoom=None, camera=None, callback=None
    ):
        if camera is not None:
            camera = check_camera_param(camera)

        if frame_number in self.keyframes.keys() and frame_number > 0:
            print(
                f"[b {orange}]Keyframe {frame_number} already exists, overwriting!"
            )

        self.keyframes[frame_number] = dict(
            zoom=zoom, camera=camera, callback=callback
        )

    def generate_frames(self, fps, duration, video):
        """
            Loop to generate frames
        """
        self.nframes = int(fps * duration)
        self.keyframes_numbers = sorted(list(self.keyframes.keys()))
        self.last_keyframe = max(self.keyframes_numbers)

        if self.last_keyframe > self.nframes:
            print(
                f"[b {orange}]The video will be {self.nframes} frames long, but you have defined keyframes after that, try increasing video duration?"
            )

        for framen in track(range(self.nframes)):
            self._make_frame(framen)
            video.addFrame()

    def get_frame_params(self, frame_number):
        if frame_number in self.keyframes_numbers:
            # Check if current frame is a key frame
            params = self.keyframes[frame_number]

        elif frame_number > self.last_keyframe:
            # check if current frame is past the last keyframe
            params = self.keyframes[self.last_keyframe]

        else:
            # interpolate between two key frames
            prev = [n for n in self.keyframes_numbers if n < frame_number][-1]
            nxt = [n for n in self.keyframes_numbers if n > frame_number][0]
            kf1, kf2 = self.keyframes[prev], self.keyframes[nxt]

            self.segment_fact = (nxt - frame_number) / (nxt - prev)

            params = dict(
                camera=self._interpolate_cameras(kf1["camera"], kf2["camera"]),
                zoom=self._interpolate_values(kf1["zoom"], kf2["zoom"]),
                callback=None,
            )
        return params

    def _make_frame(self, frame_number):
        frame_params = self.get_frame_params(frame_number)

        # callback
        if frame_params["callback"] is not None:
            frame_params["callback"](self.scene, frame_number, self.nframes)

        # render
        self.scene.render(
            camera=frame_params["camera"],
            zoom=frame_params["zoom"],
            interactive=False,
        )

    def _interpolate_cameras(self, cam1, cam2):
        if cam1 is None:
            return cam2
        elif cam2 is None:
            return cam1

        interpolated = {}
        for (k, v1), (k2, v2) in zip(cam1.items(), cam2.items()):
            if k != k2:
                raise ValueError(f"Keys mismatch: {k} - {k2}")
            interpolated[k] = self._interpolate_values(v1, v2)
        return interpolated

    def _interpolate_values(self, v1, v2):
        if v1 is None:
            return v2
        elif v2 is None:
            return v1

        return self.segment_fact * np.array(v1) + (
            1 - self.segment_fact
        ) * np.array(v2)

    # def _get_last_next(self, frame_number):
    #     raise NotImplementedError('Deal with frame being one of the specified keyframes')
    #     last = [n for n in self.key_frames_n if n<frame_number]
    #     nxt = [n for n in self.key_frames_n if n>=frame_number]

    #     if not last:
    #         return None, nxt
    #     elif not nxt:
    #         return last, None
    #     else:
    #         return last[0], nxt[0]

    # def _get_frame_params(self, last, nxt):
    #     self.segment_fact = 1 - (framen/tot_frames)
    #     kf1, kf2 = self.keyframes[last], self.keyframes[nxt]

    #     camera = self._interpolate_cameras(kf1['camera'], kf2['camera'])
    #     zoom = self._interpolate_values(kf1['zoom'], kf2['zoom'])

    #     params = dict(
    #         camera=camera,
    #         zoom=zoom,
    #         callback=None
    #     )
    #     self._last_frame_params = params
    #     return params

    # def make_frame(self):
    #     # Get previous and next keyframes
    #     last, nxt = self._get_last_next()

    #     if last is None:
    #         last = 0  # it's the first frame
    #     elif nxt is None:
    #         # just keep what was the last set of paramters.
    #         frame_params = self._last_frame_params
    #     else:
    #         frame_params = self._get_frame_params(last, nxt,)

    #     # Call frame callback
    #     if frame_params['callback'] is not None:
    #         frame_params['callback'](self.scene)

    #     # render
    #     self.scene.render(camera=frame_params['camera'], zoom=frame_params['zoom'], interactive=False)
