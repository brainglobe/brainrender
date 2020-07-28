import pytest
from brainrender.ABA.atlas_images import ImageDownload
from tempfile import TemporaryDirectory


@pytest.fixture
def imd():
    return ImageDownload()


def test_imd(imd):
    imd.get_atlas_by_name(imd.mouse_coronal)
    imd.get_products_by_species("Mouse")


def test_get_experiments(imd):
    imd.get_experimentsid_by_productid(26)


def test_get_atlas_images(imd):
    imd.get_atlasimages_by_atlasid(imd.mouse_coronal_atlas_id)
    imd.get_atlasimages_by_atlasid(imd.mouse_sagittal_atlas_id)


@pytest.mark.slow
def test_download_imgs(imd):
    tmp_dir = TemporaryDirectory()
    imd.download_images_by_atlasid(
        tmp_dir.name, imd.mouse_coronal_atlas_id, debug=True
    )
    imd.download_images_by_atlasid(
        tmp_dir.name,
        imd.mouse_sagittal_atlas_id,
        debug=True,
        downsample=4,
        snames=True,
        annotated=False,
        atlas_svg=False,
    )
    tmp_dir.cleanup()
