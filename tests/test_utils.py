# import numpy as np
from brainrender.scene import Scene
from brainrender.Utils.volume import (
    load_labelled_volume,
    extract_volume_surface,
    extract_label_mesh,
)


def test_volume_utils():
    scene = Scene()

    path = str(scene.atlas.root_dir / "annotation.tiff")

    vol = load_labelled_volume(path)
    extract_volume_surface(vol)
    extract_label_mesh(vol, 1)
