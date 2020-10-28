from pyinspect import install_traceback
import os
from pathlib import Path

install_traceback()

import brainrender.settings
from brainrender.scene import Scene
import brainrender.actors

base_dir = Path(os.path.join(os.path.expanduser("~"), ".brainrender"))
base_dir.mkdir(exist_ok=True)
