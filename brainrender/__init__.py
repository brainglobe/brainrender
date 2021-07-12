import os
from loguru import logger
import sys
from pathlib import Path
from rich.logging import RichHandler

try:
    from pyinspect import install_traceback

    install_traceback()
except ImportError:
    pass  # fails in notebooks

from brainrender import settings
from brainrender.scene import Scene
import brainrender.actors
from brainrender.video import VideoMaker, Animation

base_dir = Path(os.path.join(os.path.expanduser("~"), ".brainrender"))
base_dir.mkdir(exist_ok=True)

__version__ = "2.0.3.4"

# set logger level


def set_logging(level="INFO", path=None):
    """
    Sets loguru to save all logs to a file i
    brainrender's base directory and to print
    to stdout only logs >= to a given level
    """
    logger.remove()
    # logger.add(sys.stdout, level=level)

    path = path or str(base_dir / "log.log")
    if Path(path).exists():
        Path(path).unlink()
    logger.add(path, level="DEBUG")

    if level == "DEBUG":
        logger.configure(
            handlers=[
                {
                    "sink": RichHandler(level="WARNING", markup=True),
                    "format": "{message}",
                }
            ]
        )


if not settings.DEBUG:
    set_logging()
else:
    set_logging(level="DEBUG")
