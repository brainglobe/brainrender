from pathlib import Path

import pytest
from brainglobe_space import AnatomicalSpace
from rich import print as rprint
from vedo import Mesh

from brainrender import Scene
from brainrender._io import load_mesh_from_file
from brainrender.actor import Actor


@pytest.fixture
def mesh_actor():
    resources_dir = Path(__file__).parent.parent / "resources"
    data_path = resources_dir / "CC_134_1_ch1inj.obj"
    obj_mesh = load_mesh_from_file(data_path, color="tomato")

    return Actor(obj_mesh, name=data_path.name, br_class="from file")


def test_actor():
    s = Scene()

    s = s.root
    assert isinstance(s, Actor)
    print(s)
    str(s)
    rprint(s)

    assert isinstance(s.mesh, Mesh)
    assert s.alpha() == s.mesh.alpha()
    assert s.name == "root"
    assert s.br_class == "brain region"


@pytest.mark.parametrize(
    "axis, expected_ind",
    [
        ("z", 2),
        ("y", 1),
        ("x", 0),
        ("frontal", 2),
        ("vertical", 1),
        ("sagittal", 0),
    ],
)
def test_mirror_origin(mesh_actor, axis, expected_ind):
    original_center = mesh_actor.center
    mesh_actor.mirror(axis)
    new_center = mesh_actor.center

    assert new_center[expected_ind] == -original_center[expected_ind]


@pytest.mark.parametrize(
    "axis, expected_ind",
    [
        ("z", 2),
        ("y", 1),
        ("x", 0),
        ("frontal", 2),
        ("vertical", 1),
        ("sagittal", 0),
    ],
)
def test_mirror_around_root(mesh_actor, axis, expected_ind):
    scene = Scene()
    root_center = scene.root.center

    original_center = mesh_actor.center
    mesh_actor.mirror(axis, origin=root_center)
    new_center = mesh_actor.center

    # The new center should be the same distance from the root center as the original center
    expected_location = (
        -(original_center[expected_ind] - root_center[expected_ind])
        + root_center[expected_ind]
    )

    assert new_center[expected_ind] == pytest.approx(
        expected_location, abs=1e-3
    )


@pytest.mark.parametrize(
    "axis, expected_ind",
    [
        ("z", 2),
        ("y", 1),
        ("x", 0),
        ("frontal", 1),
        ("vertical", 0),
        ("sagittal", 2),
    ],
)
def test_mirror_custom_space(mesh_actor, axis, expected_ind):
    scene = Scene()
    scene.atlas.space = AnatomicalSpace("sra")

    original_center = mesh_actor.center
    mesh_actor.mirror(axis, atlas=scene.atlas)
    new_center = mesh_actor.center

    assert new_center[expected_ind] == -original_center[expected_ind]


@pytest.mark.parametrize(
    "axis, expected_ind",
    [
        ("z", 2),
        ("y", 1),
        ("x", 0),
        ("frontal", 1),
        ("vertical", 0),
        ("sagittal", 2),
    ],
)
def test_mirror_custom_space_around_root(mesh_actor, axis, expected_ind):
    scene = Scene()
    scene.atlas.space = AnatomicalSpace("sra")
    root_center = scene.root.center

    original_center = mesh_actor.center
    mesh_actor.mirror(axis, origin=root_center, atlas=scene.atlas)
    new_center = mesh_actor.center

    # The new center should be the same distance from the root center as the original center
    expected_location = (
        -(original_center[expected_ind] - root_center[expected_ind])
        + root_center[expected_ind]
    )

    assert new_center[expected_ind] == pytest.approx(
        expected_location, abs=1e-3
    )
