from vedo import Video as VtkVideo
from myterial import amber_light
from rich import print
from loguru import logger
import os


class Video(VtkVideo):
    # Redifine vedo.Video close method
    def __init__(self, *args, fmt="mp4", size="1620x1050", **kwargs):
        """
        Video class, takes care of storing screenshots (frames)
        as images in a temporary folder and then merging these into a
        single video file when the video is closed.
        """
        super().__init__(*args, **kwargs)
        self.format = fmt
        self.size = size

    def close(self):
        """Render the video and write to file."""
        print(f"[{amber_light}]Saving video")
        logger.debug(f"[{amber_light}]Saving video")

        fld = os.path.join(self.tmp_dir.name, "%d.png")
        fps = int(self.fps)
        name = f"{self.name}.{self.format}"
        fmt = "-vcodec libx264 -crf 28 -pix_fmt yuv420p"
        if self.size:
            fmt += f" -s {self.size}"

        command = f"ffmpeg -hide_banner -loglevel panic -y -r {fps} -start_number 0 -i {fld} {fmt} {name}"
        out = os.system(command)
        self.tmp_dir.cleanup()
        return out, command
