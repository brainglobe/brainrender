from brainrender.scene import Scene
from brainrender.video import VideoMaker, Animation
import pytest
from pathlib import Path


@pytest.mark.local
def test_video():

    s = Scene(title="BR")

    s.add_brain_region("TH")

    vm = VideoMaker(s, "tests", "test")
    savepath = vm.make_video(duration=1, fps=15, azimuth=3)

    assert savepath == "tests/test.mp4"
    path = Path(savepath)
    assert path.exists()
    path.unlink()


@pytest.mark.local
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


@pytest.mark.local
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
    assert savepath == "tests/test.mp4"
    path = Path(savepath)
    assert path.exists()
    path.unlink()
