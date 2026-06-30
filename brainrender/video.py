"""VideoMaker and Animation classes for rendering brainrender scenes to video."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from brainrender.scene import Scene

import numpy as np
from loguru import logger
from myterial import amber, orange, salmon
from rich import print
from rich.progress import track

import brainrender as br
from brainrender._jupyter import not_on_jupyter
from brainrender._video import Video
from brainrender.camera import check_camera_param, get_camera_params


class VideoMaker:
    def __init__(
        self,
        scene: Scene,
        save_fld: str | Path,
        name: str,
        fmt: str = "mp4",
        size: str = "1620x1050",
        make_frame_func: Callable[..., None] | None = None,
    ) -> None:
        """
        Create a video by animating a scene and saving a sequence of screenshots.

        Parameters
        ----------
        scene
            The instance of Scene to be animated.
        save_fld
            Where the video will be saved.
        name
            Name of the video file.
        fmt
            Video format. Default ``"mp4"``.
        size
            Size of video frames in pixels. Default ``"1620x1050"``.
        make_frame_func
            If passed, called with the Scene and current frame number at
            every frame to animate the scene. Defaults to ``_make_frame``.
        """
        logger.debug(
            f"Creating video with name {name}. Format: {fmt}, size: {size}, save folder: {save_fld}"
        )

        self.scene = scene

        self.save_fld = Path(save_fld)
        self.save_fld.mkdir(exist_ok=True)
        self.save_name = name
        self.video_format = fmt
        self.size = size
        if "mp4" not in self.video_format:
            raise NotImplementedError(
                "Video creation can only output mp4 videos for now"
            )

        self.make_frame_func = make_frame_func or self._make_frame

    @staticmethod
    def _make_frame(
        scene: Scene,
        frame_number: int,
        tot_frames: int,
        resetcam: bool,
        azimuth: int = 0,
        elevation: int = 0,
        roll: int = 0,
    ) -> None:
        """
        Default ``make_frame_func``. Rotate the camera in 3 directions.

        Parameters
        ----------
        scene
            Scene to be animated.
        frame_number
            Current frame number (unused by default).
        tot_frames
            Total number of frames.
        resetcam
            If True the camera is reset.
        azimuth
            Rotation in degrees per frame around the azimuth axis.
        elevation
            Rotation in degrees per frame around the elevation axis.
        roll
            Rotation in degrees per frame around the roll axis.
        """
        scene.plotter.show(interactive=False, resetcam=resetcam)
        scene.plotter.camera.Elevation(elevation)
        scene.plotter.camera.Azimuth(azimuth)
        scene.plotter.camera.Roll(roll)

    def generate_frames(
        self,
        fps: int,
        duration: float,
        video: Video,
        resetcam: bool,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Loop to generate frames.

        Parameters
        ----------
        fps
            Frame rate.
        duration
            Video duration in seconds.
        video
            vedo.Video instance used to create the video.
        resetcam
            If True the camera is reset.
        """
        nframes = int(fps * duration)
        for i in track(range(nframes), description="Generating frames"):
            self.make_frame_func(
                self.scene, i, nframes, resetcam, *args, **kwargs
            )
            video.add_frame()

    def compress(self, temp_name: str) -> None:
        """
        Compress the created video with ffmpeg and remove the uncompressed copy.

        Parameters
        ----------
        temp_name
            Path (without extension) of the temporary uncompressed video.
        """
        out_name = str(self.save_fld.resolve() / f"{self.save_name}.mp4")
        command = f'ffmpeg -hide_banner -loglevel panic -i "{temp_name}.mp4" -vcodec libx264 -crf 28 "{out_name}" -y'
        os.system(command)
        Path(temp_name + ".mp4").unlink()

        spath = str(
            self.save_fld.resolve() / f"{self.save_name}.{self.video_format}"
        )
        print(f"[{amber}]Saved compressed video at: [{orange} bold]{spath}")

    @not_on_jupyter
    def make_video(
        self,
        *args: Any,
        duration: float = 10,
        fps: int = 30,
        fix_camera: bool = False,
        resetcam: bool = False,
        render_kwargs: dict = {},
        **kwargs: Any,
    ) -> str:
        """
        Create a video using user-defined parameters.

        Parameters
        ----------
        *args
            Extra arguments passed to ``make_frame_func``.
        duration
            Duration of the video in seconds.
        fps
            Frame rate.
        fix_camera
            If True the focal point is fixed based on the first keyframe.
        resetcam
            If True the camera is reset between frames.
        render_kwargs
            Extra keyword arguments passed to ``scene.render``.
        **kwargs
            Extra keyword arguments passed to ``make_frame_func``.

        Returns
        -------
        str
            Path of the saved video file.
        """
        logger.debug(f"Saving a video {duration}s long ({fps} fps)")
        _off = br.settings.OFFSCREEN
        br.settings.OFFSCREEN = True  # render offscreen

        self.scene.render(interactive=False, **render_kwargs)

        if fix_camera:
            first_frame = self.keyframes.get(0)
            if not first_frame:
                logger.error("No keyframes found, can't fix camera")

            # Sets the focal point of the first frame to the centre of mass of the
            # full root mesh, since this focal point is set subsequent frames will
            # have the same focal point unless a new camera is defined
            self.keyframes[0]["camera"][
                "focal_point"
            ] = self.scene.root._mesh.center_of_mass()

        print(f"[{amber}]Saving video in [{orange}]{self.save_fld}")

        # Create video
        video = Video(
            name=str(self.save_fld.resolve() / self.save_name),
            duration=duration,
            fps=fps,
            fmt=self.video_format,
            size=self.size,
        )

        # Make frames
        self.generate_frames(fps, duration, video, resetcam, *args, **kwargs)
        self.scene.close()

        # Stitch frames into uncompressed video
        out, command = video.close()
        spath = str(
            self.save_fld.resolve() / f"{self.save_name}.{self.video_format}"
        )
        if out:
            print(
                f"[{orange} bold]ffmpeg returned an error while trying to save video with command:\n    [{salmon}]{command}"
            )
        else:
            print(f"[{amber}]Saved video at: [{orange} bold]{spath}")

        # finish up
        br.settings.OFFSCREEN = _off
        return spath


def sigma(x: float) -> float:
    """
    Sigmoid curve clamped to ``[0, 1]``.

    Parameters
    ----------
    x
        Input value.

    Returns
    -------
    float
        The sigmoid-transformed value, clamped to the range ``[0, 1]``.
    """
    y = 1.05 / (1 + np.exp(-8 * (x - 0.5))) - 0.025
    if y < 0:
        y = 0
    if y > 1:
        y = 1
    return y


class Animation(VideoMaker):
    """
    Facilitate video creation via keyframes.

    At each keyframe various parameters (e.g. camera position) are specified
    and the video is created by interpolating between consecutive keyframes.
    """

    _last_frame_params = None
    _first_zoom = 0

    def __init__(
        self,
        scene: Scene,
        save_fld: str | Path,
        name: str,
        fmt: str = "mp4",
        size: str = "1620x1050",
    ) -> None:
        """
        Parameters
        ----------
        scene
            The instance of Scene to be animated.
        save_fld
            Where the video will be saved.
        name
            Name of the video file.
        fmt
            Video format. Default ``"mp4"``.
        size
            Size of video frames in pixels. Default ``"1620x1050"``.
        """
        VideoMaker.__init__(self, scene, save_fld, name, fmt=fmt, size=size)
        logger.debug("Creating animation")

        self.keyframes = {}
        self.keyframes[0] = dict(  # make sure first frame is a keyframe
            zoom=None, camera=None, callback=None
        )
        self.keyframes_numbers = 0
        self.nframes = 0
        self.last_keyframe = 0
        self.segment_fact = 0

    def add_keyframe(
        self,
        time: float,
        duration: float = 0,
        camera: dict | None = None,
        zoom: float | None = None,
        interpol: str = "sigma",
        callback: Callable[..., dict | None] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Add a keyframe to the video.

        Parameters
        ----------
        time
            Time in seconds at which the keyframe takes place.
        duration
            If >0 the keyframe is repeated every 5ms from ``time`` to
            ``time + duration``.
        camera
            Dictionary of camera parameters.
        zoom
            Camera zoom level.
        interpol
            Interpolation mode between keyframes: ``"sigma"`` or
            ``"linear"``.
        callback
            Function taking (scene, frame_number, total_frames) as
            arguments. Used to trigger actions during a keyframe
            (e.g. removing an actor).
        **kwargs
            Extra keyword arguments passed to ``callback``.
        """
        if camera is not None:
            camera = check_camera_param(camera)

        if time in self.keyframes.keys() and time > 0:
            print(f"[b {orange}]Keyframe {time} already exists, overwriting!")

        if zoom is None:
            previous_zoom = list(self.keyframes.values())[0]["zoom"] or 0
            zoom = previous_zoom

        if not duration:
            self.keyframes[time] = dict(
                zoom=zoom,
                camera=camera,
                callback=callback,
                interpol=interpol,
                kwargs=kwargs,
            )
        else:
            for time in np.arange(time, time + duration, 0.001):
                self.keyframes[time] = dict(
                    zoom=zoom if time == 0 else None,
                    camera=camera,
                    callback=callback,
                    interpol=interpol,
                    kwargs=kwargs,
                )

    def get_keyframe_framenumber(self, fps: int) -> None:
        """
        Convert keyframe times (seconds) to frame numbers.

        Parameters
        ----------
        fps
            Frame rate.
        """
        self.keyframes = {
            int(np.floor(s * fps)): v for s, v in self.keyframes.items()
        }
        self.keyframes_numbers = sorted(list(self.keyframes.keys()))

    def generate_frames(
        self,
        fps: int,
        duration: float,
        video: Video,
        resetcam: bool,
    ) -> None:
        """
        Loop to generate frames.

        Parameters
        ----------
        fps
            Frame rate.
        duration
            Video duration in seconds.
        video
            Vedo Video instance used to create the video.
        resetcam
            If True the camera is reset.
        """
        logger.debug(
            f"Generating animation keyframes. Duration: {duration}, fps: {fps}"
        )
        self.get_keyframe_framenumber(fps)

        self.nframes = int(fps * duration)
        self.last_keyframe = max(self.keyframes_numbers)

        if self.last_keyframe > self.nframes:
            print(
                f"[b {orange}]The video will be {self.nframes} frames long, but you have defined keyframes after that, try increasing video duration?"
            )

        for framen in track(
            range(self.nframes), description="Generating frames..."
        ):
            self._make_frame(framen, resetcam)

            if framen > 1:
                video.add_frame()

    def get_frame_params(self, frame_number: int) -> dict:
        """
        Get interpolated parameters for a given frame number.

        If the frame is a keyframe or past the last keyframe, the
        corresponding keyframe params are returned directly. Otherwise
        params are interpolated using either a linear or sigmoid function.

        Parameters
        ----------
        frame_number
            Current frame number.

        Returns
        -------
        dict
            Camera and zoom parameters for this frame.
        """
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
            if kf2["interpol"] == "sigma":
                self.segment_fact = sigma(self.segment_fact)

            params = dict(
                camera=self._interpolate_cameras(kf1["camera"], kf2["camera"]),
                zoom=self._interpolate_values(kf1["zoom"], kf2["zoom"]),
                callback=None,
            )

        # get current camera (to avoid using scene's default)
        if params["camera"] is None:
            params["camera"] = get_camera_params(self.scene)
        return params

    def _make_frame(self, frame_number: int, resetcam: bool) -> None:
        """
        Create a frame with the correct params
        and call the keyframe callback function if defined.

        Parameters
        ----------
        frame_number
            Current frame number.
        resetcam
            If True the camera is reset.
        """
        frame_params = self.get_frame_params(frame_number)
        logger.debug(f"Frame {frame_number}, params: {frame_params}")

        # callback
        if frame_params["callback"] is not None:
            callback_camera = frame_params["callback"](
                self.scene,
                frame_number,
                self.nframes,
                **frame_params["kwargs"],
            )
        else:
            callback_camera = None

        # see if callback returned a camera
        camera = callback_camera or frame_params["camera"]

        # render
        self.scene.render(
            camera=camera.copy(),
            zoom=frame_params["zoom"],
            interactive=False,
            resetcam=resetcam,
        )

    def _interpolate_cameras(
        self,
        cam1: dict | None,
        cam2: dict | None,
    ) -> dict | None:
        """
        Interpolate the parameters of two cameras.

        Parameters
        ----------
        cam1
            First camera parameter dict.
        cam2
            Second camera parameter dict.

        Returns
        -------
        dict or None
            The interpolated camera parameters, or the input camera if only one
            camera is provided.
        """
        if cam1 is None:
            return cam2
        elif cam2 is None:
            return cam1

        interpolated = {}
        for k, v1 in cam1.items():
            try:
                interpolated[k] = self._interpolate_values(v1, cam2[k])
            except KeyError:  # pragma: no cover
                raise ValueError(
                    "Cameras to interpolate dont have the same set of parameters"
                )
        return interpolated

    def _interpolate_values(
        self,
        v1: float | np.ndarray | None,
        v2: float | np.ndarray | None,
    ) -> float | np.ndarray | None:
        """
        Interpolate two values using the current segment factor.

        Parameters
        ----------
        v1
            First value.
        v2
            Second value.

        Returns
        -------
        float or numpy.ndarray or None
            The interpolated value, or the input value if only one is provided.
        """
        if v1 is None:
            return v2
        elif v2 is None:
            return v1

        return self.segment_fact * np.array(v1) + (
            1 - self.segment_fact
        ) * np.array(v2)
