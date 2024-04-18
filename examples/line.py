import numpy as np
import vedo

vedo.settings.default_backend = "vtk"

from brainrender import Scene
from brainrender.actors import Points, Line

# Display the Allen Brain mouse atlas.
scene = Scene(atlas_name="allen_mouse_25um")

# Highlight the cerebral cortex.
scene.add_brain_region("CTX", alpha=0.2, color="green")

# Add two points identifying the positions of two cortical neurons.
point_coordinates = np.array([[4575, 5050, 9750], [4275, 2775, 6100]])

points = Points(point_coordinates, radius=100, colors="blue")
scene.add(points)

# Display the shortest path within cortex between the two points.
# The path was pre-calculated with https://github.com/seung-lab/dijkstra3d/.
path_coordinates = np.array(
    [
        [4575, 5050, 9750],
        [4575, 4800, 9500],
        [4575, 4550, 9250],
        [4575, 4300, 9000],
        [4575, 4050, 8750],
        [4350, 3800, 8500],
        [4225, 3550, 8250],
        [4200, 3300, 8000],
        [4200, 3100, 7750],
        [4200, 2950, 7500],
        [4200, 2800, 7250],
        [4200, 2700, 7000],
        [4200, 2650, 6750],
        [4200, 2650, 6500],
        [4200, 2650, 6250],
        [4275, 2775, 6100],
    ]
)

line = Line(path_coordinates, linewidth=3, color="black")
scene.add(line)

# Render the scene and display the figure.
scene.render()
