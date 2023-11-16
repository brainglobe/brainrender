from pathlib import Path

import pytest

from brainrender import Scene


@pytest.fixture
def scene():
    """Provide a scene with a brain region"""
    s = Scene(title="BR")
    th = s.add_brain_region("TH")
    s.add_label(th, "TH")
    return s


def test_export_for_web(scene):
    """Check that exporting to html creates the expected file"""
    path = scene.export("test.html")
    assert path == "test.html"

    path = Path(path)
    assert path.exists()

    path.unlink()


def test_export_for_web_raises(scene):
    """Check that exporting with invalid file extention raises ValueError"""
    with pytest.raises(ValueError):
        scene.export("test.py")
