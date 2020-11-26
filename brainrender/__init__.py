import os
from pathlib import Path

try:
    from pyinspect import install_traceback

    install_traceback()
except ImportError:
    pass  # fails in notebooks

import brainrender.settings
from brainrender.scene import Scene
import brainrender.actors
from brainrender.video import VideoMaker, Animation

base_dir = Path(os.path.join(os.path.expanduser("~"), ".brainrender"))
base_dir.mkdir(exist_ok=True)
