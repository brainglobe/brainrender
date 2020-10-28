from brainrender.scene import Scene
from brainrender.video import VideoMaker

from pathlib import Path


def test_video():

    s = Scene(title="BR")

    s.add_brain_region("TH")

    vm = VideoMaker(s, "tests", "test")
    savepath = vm.make_video(duration=1, fps=15, azimuth=3)

    assert savepath == "tests/test.mp4"
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

    assert savepath == "tests/test.mp4"
    path = Path(savepath)
    assert path.exists()
    path.unlink()
