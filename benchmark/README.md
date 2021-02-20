Code to evaluate how fast brainrender is and how it compares to other software.

Note: the exact duration on your system will depend on various factors like if other processes are
running or the size of the rendering window/screen.

Note: the duration reported in the results does not include scene creation (`scene = Scene()`) which takes <2s and mst of this time is spent accessing atlas data.

## Machines tested
* **[1]** macOS - Mojave 10.14.6 - MacBook Pro (15-inch, 2019) - 2.3 GHz Intel Core i9 - Radeon Pro 560X 4 GB GPU

## Tests
### N cells
Render N cells + the root object. The timer counts how long it takes to create a Points actor
representing N cells, adding this to a scene and rendering the scene full screen/

### Slice N cells
Render N cells + the root object and slice them. The timer counts how long it takes to create a Points actor
representing N cells, adding this to a scene and slicing the actor + the root mesh
through the midline, as well as rendering the scene full screen.

### Brain regions
Render >1k brain region meshes. Measures how long it takes to fetch and render the meshes
for almost all brain regions in the mouse brain. 

### Animation
Make a short animation

### Volume
Parse a numpy array to create a Volume actor (10 times) and render

## Results
| Test | Machine | GPU | # actors | # vertices | FPS | run duration | benchmark file |
| ---- |:-------:|:---:|:--------:|:----------:|:---:|:------------:| --------------:|
| 10k cells | [1] | yes | 3 | 1029324 | 24.76 | 0.81s | bm_cells.py |
| 100k cells | [1] | yes | 3 | 9849324 | 18.87 | 3.23s | bm_cells.py |
| 1M cells | [1] | yes | 3 | 98049324 | 2.65 | 31.01s | bm_cells.py |
| Slicing 10k cells | [1] | yes | 3 | 237751 | 37.64 | 0.96s | bm_cells.py |
| Slicing 100k cells | [1] | yes | 3 | 276092 | 31.79 | 7.77s | bm_cells.py |
| Slicing 1M cells | [1] | yes | 3 | 275069 | 11.23 | 91.31s | bm_cells.py |
| brain regions | [1] | yes | 1678 | 1864388 | 9.38 | 11.78s | bm_brain_regions.py |
| animation | [1] | yes | 8 | 96615 | 9.91 | 18.98s | bm_animation.py |
| volume | [1] | yes | 12 | 49324 | 1.79 | 2.31s | bm_volume.py |

Note: Volume actors don't have a number of "vertices" so are not counted here