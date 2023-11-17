import numpy as np
import pytest

from brainrender import Scene
from brainrender.actors import Points


def get_n_points_in_region(region, N):
    """
    Gets N points inside (or on the surface) of a mes
    """

    region_bounds = region.mesh.bounds()
    X = np.linspace(region_bounds[0], region_bounds[1], num=N)
    Y = np.linspace(region_bounds[2], region_bounds[3], num=N)
    Z = np.linspace(region_bounds[4], region_bounds[5], num=N)
    pts = [[x, y, z] for x, y, z in zip(X, Y, Z)]

    ipts = region.mesh.inside_points(pts).points()
    return np.vstack(ipts)


def check_bounds(bounds, parent_bounds):
    """
    Checks that the bounds of an actor are within the bounds of the root
    """
    for i, bound in enumerate(bounds):
        if i % 2 == 0:
            assert bound >= parent_bounds[i]
        else:
            assert bound <= parent_bounds[i]


@pytest.fixture
def scene():
    scene = Scene(inset=False)
    yield scene
    del scene


def test_scene_with_brain_region(scene):
    brain_region = scene.add_brain_region(
        "grey",
        alpha=0.4,
    )

    bounds = brain_region.bounds()
    root_bounds = scene.root.bounds()

    assert scene.actors[1] == brain_region

    check_bounds(bounds, root_bounds)


def test_add_cells(scene):
    mos = scene.add_brain_region("MOs", alpha=0.15)
    coordinates = get_n_points_in_region(mos, 1000)
    points = Points(coordinates, name="CELLS", colors="steelblue")

    scene.add(points)

    assert scene.actors[0] == scene.root
    assert scene.actors[1] == mos
    assert scene.actors[2] == points

    scene.render(interactive=False)

    root_bounds = scene.root.bounds()
    region_bounds = mos.bounds()
    points_bounds = points.bounds()

    check_bounds(points_bounds, root_bounds)
    check_bounds(region_bounds, root_bounds)


def test_add_labels(scene):
    th, mos = scene.add_brain_region("TH", "MOs")
    scene.add_label(th, "TH")

    scene.render(interactive=False)

    assert scene.actors[1] == th
    assert scene.actors[2] == mos
    assert len(th.labels) == 2
    assert len(mos.labels) == 0

    th_label_text_bounds = th.labels[0].bounds()
    th_label_bounds = th.labels[1].bounds()
    root_bounds = scene.root.bounds()

    check_bounds(th_label_text_bounds, root_bounds)
    check_bounds(th_label_bounds, root_bounds)


def test_add_mesh_from_file(scene, pytestconfig):
    root_path = pytestconfig.rootpath
    scene.add_brain_region("SCm", alpha=0.2)
    scene.add(
        root_path / "tests" / "files" / "CC_134_1_ch1inj.obj", color="tomato"
    )
