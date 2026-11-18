import platform
from pathlib import Path

import pytest
from skimage.color import rgb2gray
from skimage.io import imread
from skimage.metrics import structural_similarity as ssim
from vedo import settings as vsettings

from brainrender import Scene, settings

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

        if platform.system() != "Linux":
            # The screenshots are not produced correctly on Linux in CI
            data_range = validate_image.max() - validate_image.min()
            similarity_index, _ = ssim(
                test_image, validate_image, data_range=data_range, full=True
            )

            assert similarity_index > similarity_threshold


@pytest.mark.parametrize(
    "brainrender_setting, vedo_setting",
    [(False, False), (True, False), (False, True), (True, True)],
)
def test_screenshot_transparent_background(
    tmp_path, monkeypatch, brainrender_setting, vedo_setting
):
    """Transparent if either brainrender's or vedo's setting is True."""
    monkeypatch.setattr(
        settings, "SCREENSHOT_TRANSPARENT_BACKGROUND", brainrender_setting
    )
    monkeypatch.setattr(
        vsettings, "screenshot_transparent_background", vedo_setting
    )
    scene = Scene(screenshots_folder=tmp_path)
    scene.add_brain_region("TH")
    scene.render(interactive=False, zoom=2)
    savepath = scene.screenshot(name="screenshot.png")
    scene.close()

    # vedo's own setting is left untouched
    assert vsettings.screenshot_transparent_background is vedo_setting

    image = imread(savepath)
    if brainrender_setting or vedo_setting:
        assert image.shape[-1] == 4
        assert (image[..., 3] == 0).any()
    else:
        assert image.shape[-1] == 3 or (image[..., 3] == 255).all()
