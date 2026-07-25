"""Thin wrapper around vedo.Video for rendering brainrender scenes to video."""

import os
from typing import Any

from loguru import logger
from myterial import amber_light
from rich import print
from vedo import Video as VtkVideo


class Video(VtkVideo):
    def __init__(
        self,
        *args: Any,
        fmt: str = "mp4",
        size: str = "1620x1050",
        **kwargs: Any,
    ) -> None:
        """
        Store screenshots as frames and merge them into a video on close.

        Parameters
        ----------
        *args
            Positional arguments forwarded to ``vedo.Video``.
        fmt
            Video format. Default ``"mp4"``.
        size
            Frame size in pixels. Default ``"1620x1050"``.
        **kwargs
            Keyword arguments forwarded to ``vedo.Video``.
        """
        super().__init__(*args, **kwargs)
        self.format = fmt
        self.size = size

    def close(self) -> tuple[int, str]:
        """
        Render the video and write to file.

        Returns
        -------
        tuple
            The FFmpeg exit code and the executed command string.
        """
        print(f"[{amber_light}]Saving video")
        logger.debug(f"[{amber_light}]Saving video")

        fld = os.path.join(self.tmp_dir.name, "%d.png")
        fps = int(self.fps)
        name = f"{self.name}.{self.format}"
        fmt = "-vcodec libx264 -crf 28 -pix_fmt yuv420p"
        if self.size:
            fmt += f" -s {self.size}"

        command = f'ffmpeg -hide_banner -loglevel panic -y -r {fps} -start_number 0 -i "{fld}" {fmt} "{name}"'
        out = os.system(command)
        self.tmp_dir.cleanup()
        return out, command
