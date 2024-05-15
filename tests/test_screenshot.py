from pathlib import Path

from myterial import orange, salmon
from rich import print
from PIL import Image
from brainrender import Scene

def test_screenshot(tmp_path):
    filename = "screenshot.png"
    scene = Scene(
        screenshots_folder=tmp_path,
    )
    scene.add_brain_region("TH")
    scene.render(interactive=False, zoom=2)
    scene.screenshot(name=filename)
    scene.close()

    test_filepath = tmp_path / filename
    assert test_filepath.exists()

    img1 = Image.open(test_filepath)
    assert img1.size == (1600, 1200)
