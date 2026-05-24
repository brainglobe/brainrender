from pathlib import Path
from unittest.mock import patch

from brainrender.scene import Scene
from brainrender.video import Animation, VideoMaker


def test_video():
    s = Scene(title="BR")

    s.add_brain_region("TH")

    vm = VideoMaker(s, "tests", "test")
    savepath = vm.make_video(duration=1, fps=15, azimuth=3)

    assert savepath == str(Path("tests").resolve() / "test.mp4")
    path = Path(savepath)
    assert path.exists()
    path.unlink()


def test_video_custom():
    def custom(scene, *args, **kwargs):
        return

    s = Scene(title="BR")

    s.add_brain_region("TH")

    vm = VideoMaker(s, "tests", "test", make_frame_func=custom)

    savepath = vm.make_video(duration=1, fps=15, azimuth=3)

    assert savepath == str(Path("tests").resolve() / "test.mp4")
    path = Path(savepath)
    assert path.exists()
    path.unlink()


def test_animation():
    # Create a brainrender scene
    scene = Scene(title="brain regions", inset=False)

    # Add brain regions
    scene.add_brain_region("TH")

    anim = Animation(scene, "tests", "test")
    anim.add_keyframe(0, camera="top", zoom=1.3)
    anim.add_keyframe(1, camera="sagittal", zoom=2.1)
    anim.add_keyframe(2, camera="frontal", zoom=3)
    anim.add_keyframe(3, camera="frontal", zoom=2)
    anim.add_keyframe(3, camera="frontal", zoom=2)  # overwrite
    anim.add_keyframe(30, camera="frontal", zoom=2)  # too many

    savepath = anim.make_video(duration=3, fps=10)
    assert savepath == str(Path("tests").resolve() / "test.mp4")
    path = Path(savepath)
    assert path.exists()
    path.unlink()


def test_compress(tmp_path):
    """Test that compress() builds correct absolute paths without os.chdir."""
    s = Scene(title="BR")
    vm = VideoMaker(s, tmp_path, "myvideo")

    # Create a fake uncompressed mp4 so Path.unlink() has something to remove
    fake_mp4 = tmp_path / "temp_video.mp4"
    fake_mp4.touch()

    with (
        patch("os.system") as mock_system,
        patch.object(vm.scene.plotter, "close", return_value=None),
    ):
        mock_system.return_value = 0
        vm.compress(str(tmp_path / "temp_video"))

    # os.system was called once with absolute paths
    assert mock_system.call_count == 1
    cmd = mock_system.call_args[0][0]

    expected_input = str((tmp_path / "temp_video.mp4").resolve())
    expected_output = str((tmp_path / "myvideo.mp4").resolve())

    assert expected_input in cmd, f"Input path missing from ffmpeg cmd: {cmd}"
    assert (
        expected_output in cmd
    ), f"Output path missing from ffmpeg cmd: {cmd}"
    # No bare filenames — must be absolute paths
    assert "myvideo.mp4" not in cmd.replace(expected_output, "")
