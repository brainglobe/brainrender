from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from brainrender import Scene

validate_directory = Path(__file__).parent / "data"


@pytest.mark.parametrize("extension", ["png", "jpg", "svg", "eps", "pdf"])
def test_screenshot(tmp_path, extension):
    filename = "screenshot." + extension
    scene = Scene(
        screenshots_folder=tmp_path,
    )
    scene.add_brain_region("TH")
    scene.render(interactive=False, zoom=2)
    scene.screenshot(name=filename)
    scene.close()

    test_filepath = tmp_path / filename

    # These are saved compressed
    if extension in ["eps", "svg"]:
        test_filepath = test_filepath.parent / (test_filepath.name + ".gz")

    assert test_filepath.exists()

    # These are the only raster formats
    if extension in ["png", "jpg"]:
        test_image = Image.open(test_filepath)
        validate_filepath = validate_directory / filename
        validate_image = Image.open(validate_filepath)

        assert test_image.size == validate_image.size

        np.testing.assert_array_almost_equal(
            np.asarray(test_image), np.asarray(validate_image), decimal=2
        )
