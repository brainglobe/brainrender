import random
from importlib.resources import files

import numpy as np
import pytest

from brainrender import Scene
from brainrender.actor import Actor
from brainrender.actors import Point, Points, PointsDensity


def get_n_random_points_in_region(region, N):
    """
    Gets N random points inside (or on the surface) of a mes
    """

    region_bounds = region.mesh.bounds()
    X = np.random.randint(region_bounds[0], region_bounds[1], size=10000)
    Y = np.random.randint(region_bounds[2], region_bounds[3], size=10000)
    Z = np.random.randint(region_bounds[4], region_bounds[5], size=10000)
    pts = [[x, y, z] for x, y, z in zip(X, Y, Z)]

    ipts = region.mesh.inside_points(pts).points()
    return np.vstack(random.choices(ipts, k=N))


def test_points_working():
    s = Scene(title="BR")
    data_path = files("brainrender").joinpath("resources/random_cells.npy")
    act = Points(np.load(data_path))
    act2 = Points(data_path, colors="k")
    act3 = Points(data_path, name="test")
    assert act3.name == "test"

    s.add(act)
    s.add(act2)

    point = Point([100, 233, 422])
    s.add(point)
    assert isinstance(point, Actor)
    assert isinstance(act, Actor)
    assert isinstance(act2, Actor)
    assert isinstance(act3, Actor)
    assert point.name == "Point"

    del s


def test_points_density():
    s = Scene(title="BR")
    mos = s.add_brain_region("MOs", alpha=0.0)
    coordinates = get_n_random_points_in_region(mos, 2000)
    pd = s.add(PointsDensity(coordinates))

    assert isinstance(pd, Actor)
    del s


def test_points_error():
    with pytest.raises(FileExistsError):
        Points(
            files("brainrender").joinpath("resources/testsfsdfs.npy"),
            colors="k",
        )
    with pytest.raises(NotImplementedError):
        Points(
            files("brainrender").joinpath("resources/random_cells.h5"),
            colors="k",
        )
