import meshio
import numpy as np
import pytest
from vedo import Mesh
from vedo.colors import get_color

from brainrender._io import convert_meshio_to_vedo

points = np.array(
    [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
)
triangles = np.array([[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]])


@pytest.fixture
def meshio_mesh():
    return meshio.Mesh(points, [("triangle", triangles)])


def test_convert_meshio_to_vedo(meshio_mesh):
    actor = convert_meshio_to_vedo(meshio_mesh)

    assert isinstance(actor, Mesh)
    assert np.allclose(actor.vertices, points)
    assert np.array_equal(np.array(actor.cells), triangles)


def test_convert_meshio_to_vedo_color_and_alpha(meshio_mesh):
    actor = convert_meshio_to_vedo(meshio_mesh, color="red", alpha=0.4)

    assert np.allclose(actor.color(), get_color("red"))
    assert actor.alpha() == pytest.approx(0.4)


def test_convert_meshio_to_vedo_ignores_non_triangle_cells():
    mesh = meshio.Mesh(
        points, [("line", np.array([[0, 1]])), ("triangle", triangles)]
    )
    actor = convert_meshio_to_vedo(mesh)

    assert actor.ncells == len(triangles)
