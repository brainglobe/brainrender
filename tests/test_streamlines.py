import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from brainrender.atlas_specific import get_streamlines_for_region
from brainrender.atlas_specific.allen_brain_atlas.streamlines import (
    _get_injection_site_um,
    _get_ml_extent_um,
    _skeleton_to_dataframe,
    get_streamlines_data,
)

ML_EXTENT = 11400.0


@pytest.fixture(autouse=True)
def _reset_ml_cache():
    import brainrender.atlas_specific.allen_brain_atlas.streamlines as _mod

    _mod._ml_extent_um_cache = None
    yield
    _mod._ml_extent_um_cache = None


def _make_fake_skeleton():
    verts = np.array([[1000.0, 2000.0, 3000.0]] * 4, dtype=float)
    comp1 = MagicMock()
    comp1.vertices = verts[:2]
    comp2 = MagicMock()
    comp2.vertices = verts[2:]
    skeleton = MagicMock()
    skeleton.vertices = verts
    skeleton.components.return_value = [comp1, comp2]
    return skeleton


@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines.BrainGlobeAtlas"
)
def test_get_ml_extent_um(mock_atlas_cls):
    mock_atlas = MagicMock()
    mock_atlas.shape = (528, 320, 456)
    mock_atlas.resolution = (25, 25, 25)
    mock_atlas_cls.return_value = mock_atlas
    result = _get_ml_extent_um()
    assert result == pytest.approx(456 * 25)


@patch("brainrender.atlas_specific.allen_brain_atlas.streamlines.requests.get")
def test_get_injection_site_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "success": True,
        "num_rows": 1,
        "msg": [
            {
                "max_voxel_x": 100.0,
                "max_voxel_y": 200.0,
                "max_voxel_z": 300.0,
            }
        ],
    }
    mock_get.return_value = mock_resp
    result = _get_injection_site_um(12345, ML_EXTENT)
    assert result is not None
    assert result["x"] == pytest.approx(100.0)
    assert result["y"] == pytest.approx(200.0)
    assert result["z"] == pytest.approx(ML_EXTENT - 300.0)


@patch("brainrender.atlas_specific.allen_brain_atlas.streamlines.requests.get")
def test_get_injection_site_empty_response(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"success": True, "num_rows": 0, "msg": []}
    mock_get.return_value = mock_resp
    assert _get_injection_site_um(12345, ML_EXTENT) is None


@patch("brainrender.atlas_specific.allen_brain_atlas.streamlines.requests.get")
def test_get_injection_site_network_error(mock_get):
    mock_get.side_effect = Exception("timeout")
    assert _get_injection_site_um(12345, ML_EXTENT) is None


@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines._get_injection_site_um"
)
def test_skeleton_to_dataframe_with_injection(mock_inj):
    mock_inj.return_value = {"x": 10.0, "y": 20.0, "z": 30.0}
    skeleton = _make_fake_skeleton()
    df = _skeleton_to_dataframe(skeleton, 99, ML_EXTENT)
    assert isinstance(df, pd.DataFrame)
    assert "lines" in df.columns
    assert "injection_sites" in df.columns
    lines = df["lines"].iloc[0]
    assert len(lines) == 2
    pt = lines[0][0]
    assert set(pt.keys()) == {"x", "y", "z"}
    assert pt["x"] == pytest.approx(1.0)
    assert pt["y"] == pytest.approx(2.0)
    assert pt["z"] == pytest.approx(ML_EXTENT - 3.0)
    assert df["injection_sites"].iloc[0] == [{"x": 10.0, "y": 20.0, "z": 30.0}]


@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines._get_injection_site_um"
)
def test_skeleton_to_dataframe_fallback_centroid(mock_inj):
    mock_inj.return_value = None
    skeleton = _make_fake_skeleton()
    df = _skeleton_to_dataframe(skeleton, 99, ML_EXTENT)
    injection = df["injection_sites"].iloc[0][0]
    assert set(injection.keys()) == {"x", "y", "z"}
    assert injection["x"] == pytest.approx(1.0)
    assert injection["y"] == pytest.approx(2.0)
    assert injection["z"] == pytest.approx(ML_EXTENT - 3.0)


@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines._get_ml_extent_um"
)
@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines.cloudvolume_installed",
    True,
)
@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines._skeleton_to_dataframe"
)
def test_get_streamlines_data_downloads(mock_s2df, mock_ml):
    mock_ml.return_value = ML_EXTENT
    fake_df = pd.DataFrame({"lines": [[]], "injection_sites": [[]]})
    mock_s2df.return_value = fake_df
    mock_cv_module = MagicMock()
    mock_cv_instance = MagicMock()
    mock_cv_instance.skeleton.get.return_value = _make_fake_skeleton()
    mock_cv_module.CloudVolume.return_value = mock_cv_instance
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch(
            "brainrender.atlas_specific.allen_brain_atlas.streamlines.streamlines_folder",
            Path(tmpdir),
        ):
            with patch.dict("sys.modules", {"cloudvolume": mock_cv_module}):
                with patch(
                    "brainrender.atlas_specific.allen_brain_atlas.streamlines.cloudvolume",
                    mock_cv_module,
                    create=True,
                ):
                    result = get_streamlines_data(
                        [111, 222], force_download=True
                    )
    assert len(result) == 2
    assert all(isinstance(r, pd.DataFrame) for r in result)


@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines._get_ml_extent_um"
)
@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines.cloudvolume_installed",
    True,
)
def test_get_streamlines_data_uses_cache(mock_ml):
    mock_ml.return_value = ML_EXTENT
    fake_df = pd.DataFrame(
        {"lines": [[[]]], "injection_sites": [[{"x": 1, "y": 2, "z": 3}]]}
    )
    mock_cv_module = MagicMock()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_df.to_json(str(Path(tmpdir) / "111.json"))
        with patch(
            "brainrender.atlas_specific.allen_brain_atlas.streamlines.streamlines_folder",
            Path(tmpdir),
        ):
            with patch(
                "brainrender.atlas_specific.allen_brain_atlas.streamlines.cloudvolume",
                mock_cv_module,
                create=True,
            ):
                result = get_streamlines_data([111], force_download=False)
    mock_cv_module.CloudVolume.return_value.skeleton.get.assert_not_called()
    assert len(result) == 1


@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines.cloudvolume_installed",
    False,
)
def test_get_streamlines_data_no_cloudvolume():
    assert get_streamlines_data([111]) == []


@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines._get_ml_extent_um"
)
@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines.cloudvolume_installed",
    True,
)
def test_get_streamlines_data_skips_failed_experiment(mock_ml):
    mock_ml.return_value = ML_EXTENT
    mock_cv_module = MagicMock()
    mock_cv_instance = MagicMock()
    mock_cv_instance.skeleton.get.side_effect = Exception("not found")
    mock_cv_module.CloudVolume.return_value = mock_cv_instance
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch(
            "brainrender.atlas_specific.allen_brain_atlas.streamlines.streamlines_folder",
            Path(tmpdir),
        ):
            with patch(
                "brainrender.atlas_specific.allen_brain_atlas.streamlines.cloudvolume",
                mock_cv_module,
                create=True,
            ):
                result = get_streamlines_data([999], force_download=True)
    assert result == []


@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines.experiments_source_search"
)
def test_get_streamlines_for_region_no_experiments(mock_search):
    mock_search.return_value = pd.DataFrame()
    assert get_streamlines_for_region("XYZ") is None


@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines.get_streamlines_data"
)
@patch(
    "brainrender.atlas_specific.allen_brain_atlas.streamlines.experiments_source_search"
)
def test_get_streamlines_for_region_calls_download(mock_search, mock_dl):
    mock_search.return_value = pd.DataFrame({"id": [111, 222]})
    mock_dl.return_value = ["df1", "df2"]
    result = get_streamlines_for_region("TH")
    assert result == ["df1", "df2"]
    mock_dl.assert_called_once()


@pytest.mark.parametrize(
    "eid",
    [479983421],
)
def test_download_streamlines_from_gcs(eid):
    """Smoke test: download one small experiment to verify the GCS source is live."""
    data = get_streamlines_data([eid], force_download=True)
    assert len(data) == 1
    df = data[0]
    assert "lines" in df.columns
    assert "injection_sites" in df.columns
    lines = df["lines"].iloc[0]
    assert len(lines) > 0
    assert set(lines[0][0].keys()) == {"x", "y", "z"}


def test_streamlines_hemisphere_orientation():
    """Verify that a right-hemisphere experiment renders in the correct hemisphere.

    Experiment 298004028 has injection at ML=2.15mm (right hemisphere) with
    near-zero left hemisphere projection volume per the Allen connectivity viewer.
    After the Z (ML) axis flip, all streamline Z coordinates should be below
    the atlas midline (~5700um), matching brainrender's right hemisphere convention.
    """
    data = get_streamlines_data([298004028], force_download=True)
    assert len(data) == 1
    lines = data[0]["lines"].iloc[0]
    assert len(lines) > 0

    # Collect all Z coordinates from all streamline components
    all_z = [pt["z"] for component in lines for pt in component]

    # Allen CCF ML extent is 11400um, midline is ~5700um
    # Right hemisphere in brainrender = Z < midline after flip
    midline = 5700.0
    right_side = [z for z in all_z if z < midline]
    assert len(right_side) / len(all_z) > 0.95, (
        f"Expected >95% of streamline points in right hemisphere (Z < {midline}), "
        f"got {len(right_side)}/{len(all_z)} ({100*len(right_side)/len(all_z):.1f}%)"
    )
