from BrainRender.scene import Scene
from BrainRender.settings import *
from BrainRender.variables import *
from time import time

import numpy as np

N_points = 10000

scene = Scene()

start_time = time()
x0, x1 = scene.root_bounds['x']
y0, y1 = scene.root_bounds['y']
z0, z1 = scene.root_bounds['z']


for i in range(N_points):
    x, y, z = np.random.randint(x0, x1), np.random.randint(y0, y1), np.random.randint(z0, z1)
    scene.add_sphere_at_point(pos=[x, y, z])

elapsed_time = time() - start_time
print("Displayed {} spheres in {} seconds".format(N_points, round(elapsed_time, 2)))

scene.render()
