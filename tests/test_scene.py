from brainrender import Scene
from brainrender.actor import Actor


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
    th = scene.add_brain_regions("TH")
    assert scene.actors[-1] == th
    assert isinstance(th, Actor)

    regs = scene.add_brain_regions("MOs", "CA1")
    assert isinstance(regs, list)
    assert len(regs) == 2

    noone = scene.add_brain_regions("what is this")
    assert noone is None


def test_add_from_files():
    scene = Scene()
    obj = scene.add("tests/files/CC_134_1_ch1inj.obj")
    assert isinstance(obj, Actor)
