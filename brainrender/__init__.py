import os
from loguru import logger
from pathlib import Path
from rich.logging import RichHandler
from importlib.metadata import PackageNotFoundError, version
from brainrender import settings

try:
    from pyinspect import install_traceback

    install_traceback(hide_locals=not settings.DEBUG)
except ImportError:
    pass  # fails in notebooks

from brainrender.scene import Scene
import brainrender.actors
from brainrender.video import VideoMaker, Animation
from brainrender.atlas import Atlas


try:
    __version__ = version("brainrender")
except PackageNotFoundError:
    # package is not installed
    pass

base_dir = Path(os.path.join(os.path.expanduser("~"), ".brainrender"))
base_dir.mkdir(exist_ok=True)


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
