from benchmark.timer import Timer
from brainrender import Scene, actors
import numpy as np
import random

# create N random cells coordinates


def get_n_random_points_in_region(region, N):
    """
    Gets N random points inside (or on the surface) of a mes
    """

    region_bounds = region.mesh.bounds()
    X = np.random.randint(region_bounds[0], region_bounds[1], size=10000)
    Y = np.random.randint(region_bounds[2], region_bounds[3], size=10000)
    Z = np.random.randint(region_bounds[4], region_bounds[5], size=10000)
    pts = [[x, y, z] for x, y, z in zip(X, Y, Z)]

    ipts = region.mesh.insidePoints(pts).points()
    return np.vstack(random.choices(ipts, k=N))


for N_cells in (10000, 100000, 1000000):
    scene = Scene(inset=False)
    coordinates = get_n_random_points_in_region(scene.root, N_cells)

    with Timer(scene, name=f"Rendering {N_cells} cells"):
        scene.add(actors.Points(coordinates))

    scene = Scene(inset=False)
    with Timer(scene, name=f"Slicing {N_cells} cells"):
        scene.add(actors.Points(coordinates))
        scene.slice("sagittal")

    scene.close()
