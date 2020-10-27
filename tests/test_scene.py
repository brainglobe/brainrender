from brainrender import Scene
from brainrender.actor import Actor
import pytest
import shutil


def test_scene_creation():
    scene = Scene(root=False)
    scene.root
    assert scene.root.alpha() == 0

    scene = Scene(atlas_name="mpin_zfish_1um")
    assert isinstance(scene.root, Actor)

    noinset = Scene(inset=False)
    noinset.root

    Scene(title="BR")


def test_scene_specials():
    scene = Scene()
    print(scene)
    assert (
        str(scene)
        == f"A `brainrender.scene.Scene` with {len(scene.actors)} actors."
    )
    scene.content
    del scene


def test_brain_regions():
    scene = Scene()
    th = scene.add_brain_region("TH")
    assert scene.actors[-1] == th
    assert isinstance(th, Actor)

    regs = scene.add_brain_region("MOs", "CA1")
    assert isinstance(regs, list)
    assert len(regs) == 2

    noone = scene.add_brain_region("what is this")
    assert noone is None

    a1 = scene.add_brain_region("TH", hemisphere="left")
    a2 = scene.add_brain_region("CA1", hemisphere="right")
    assert isinstance(a1, Actor)
    assert isinstance(a2, Actor)


def test_add_from_files():
    scene = Scene()
    obj = scene.add("tests/files/CC_134_1_ch1inj.obj", color="red")
    obj = scene.add("tests/files/CC_134_1_ch1inj.obj", alpha=0.2)
    assert isinstance(obj, Actor)


def test_labels():
    scene = Scene()
    th = scene.add_brain_region("TH")
    scene.add_label(th, "TH")
    scene.render(interactive=False)


def test_scene_render():
    scene = Scene()
    scene.add_brain_region("TH")

    scene.render(interactive=False, zoom=1.4)


def test_scene_slice():
    s = Scene()
    s.add_brain_region("TH")

    s.slice("frontal")

    ret = s.slice("frontal",)
    assert ret is None

    s.slice("sagittal", close_actors=True)

    s = Scene()
    th = s.add_brain_region("TH")

    plane = s.atlas.get_plane(pos=[1999, 1312, 3421], norm=[1, -1, 2])
    s.slice(plane, actors=th)
    ret = s.slice(plane, actors=[th, s.root],)


@pytest.mark.parametrize(
    "name, scale", [("test", 2), (None, None), (None, 1), ("test2", None)]
)
def test_scene_screenshot(name, scale):
    s = Scene(screenshots_folder="tests/screenshots")
    s.screenshot(name=name, scale=scale)
    shutil.rmtree("tests/screenshots")
