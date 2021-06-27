from brainrender import Scene
from brainrender.actor import Actor
import pytest
import shutil


def test_scene_creation():
    scene = Scene(root=False)
    scene.root
    noinset = Scene(inset=False, title="TEST")
    noinset.root


def test_scene_render_simple():
    scene = Scene()
    scene.render(interactive=False)


def test_scene_specials():
    scene = Scene()
    print(scene)
    str(scene)
    scene.content


def test_brain_regions():
    scene = Scene()
    th = scene.add_brain_region("TH")
    assert scene.actors[-1] == th
    assert isinstance(th, Actor)

    regs = scene.add_brain_region("MOs", "CA1")
    assert isinstance(regs, list)
    assert len(regs) == 2

    nan = scene.add_brain_region("MOs", "CA1")
    assert nan is None
    noone = scene.add_brain_region("what is this")
    assert noone is None

    scene.add_brain_region("TH", hemisphere="left")
    scene.add_brain_region("CA1", hemisphere="right")
    scene.add_brain_region("STN", hemisphere="right")


def test_labels():
    scene = Scene()
    th = scene.add_brain_region("TH")
    scene.add_label(th, "TH")


def test_scene_render():
    scene = Scene()
    scene.add_brain_region("TH")

    scene.render(interactive=False, zoom=1.4)

    scene.render(
        interactive=False,
        camera=dict(
            pos=(
                10705.845660949382,
                7435.678067378925,
                -36936.3695486442,
            ),
            viewup=(
                -0.0050579179155257475,
                -0.9965615097647067,
                -0.08270172139591858,
            ),
            clippingRange=(30461.81976236306, 58824.38622122339),
        ),
    )


def test_scene_slice():
    s = Scene()
    s.add_brain_region("TH")

    s.slice("frontal")

    ret = s.slice(
        "frontal",
    )
    assert ret is None

    s.slice("sagittal", close_actors=True)

    s = Scene()
    th = s.add_brain_region("TH")

    plane = s.atlas.get_plane(pos=[1999, 1312, 3421], norm=[1, -1, 2])
    s.slice(plane, actors=th)
    ret = s.slice(
        plane,
        actors=[th, s.root],
    )
    del s


@pytest.mark.parametrize(
    "name, scale", [("test", 2), (None, None), (None, 1), ("test2", None)]
)
def test_scene_screenshot(name, scale):
    s = Scene(screenshots_folder="tests/screenshots")
    s.screenshot(name=name, scale=scale)
    shutil.rmtree("tests/screenshots")
    del s


def test_actor_removal():
    s = Scene()
    th = s.add_brain_region("TH")
    assert len(s.actors) == 2

    s.remove(th)
    assert len(s.actors) == 1

    s.remove("no actor")
    assert len(s.actors) == 1


def test_get_actors():
    s = Scene()
    th = s.add_brain_region("TH")

    found1 = s.get_actors(name="TH")
    assert len(found1) == 1
    assert th in found1

    found2 = s.get_actors(br_class="brain region")
    assert len(found2) == 2
    assert th in found2
    assert s.root in found2
