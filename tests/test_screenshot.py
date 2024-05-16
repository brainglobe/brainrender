from pathlib import Path

import pytest
from skimage.color import rgb2gray
from skimage.io import imread
from skimage.metrics import structural_similarity as ssim

from brainrender import Scene

validate_directory = Path(__file__).parent / "data"


@pytest.mark.parametrize("extension", ["png", "jpg", "svg", "eps", "pdf"])
def test_screenshot(tmp_path, extension, similarity_threshold=0.75):
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
        test_image = rgb2gray(imread(test_filepath))
        validate_filepath = validate_directory / filename
        validate_image = rgb2gray(imread(validate_filepath))

        assert test_image.shape == validate_image.shape

        data_range = validate_image.max() - validate_image.min()
        similarity_index, _ = ssim(
            test_image, validate_image, data_range=data_range, full=True
        )

        assert similarity_index > similarity_threshold
