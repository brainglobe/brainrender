from brainrender.atlas import Atlas


def test_atlas_download():
    """
    Just downloads the test atlas to ensure
    the data is available in GitHub actions
    """
    atlas = Atlas()
    assert atlas.atlas_name == "allen_mouse_100um"
