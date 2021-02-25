from brainrender import Scene
from pathlib import Path
import pytest


@pytest.mark.local
def test_export_for_web():
    s = Scene(title="BR")

    th = s.add_brain_region("TH")

    s.add_label(th, "TH")

    path = s.export("test.html")
    assert path == "test.html"

    path = Path(path)
    assert path.exists()

    path.unlink()

    with pytest.raises(ValueError):
        path = s.export("test.py")
