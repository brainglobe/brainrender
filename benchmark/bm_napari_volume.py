import numpy as np
from benchmark.timer import SimpleTimer
import napari

data = np.load("benchmark/volume.npy")

timer = SimpleTimer("napari volume")
with napari.gui_qt():
    print("creating viewer")
    viewer = napari.Viewer(ndisplay=3)

    timer.start()
    for i in range(10):
        viewer.add_image(data)
    timer.stop()
