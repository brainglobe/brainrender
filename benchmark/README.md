 TheseCode to evaluate how fast brainrender is and how it compares to other software.

Note: the exact duration on your system will depend on various factors like if other processes are
running or the size of the rendering window/screen.

Note: the duration reported in the results does not include scene creation (`scene = Scene()`) which takes <2s and mst of this time is spent accessing atlas data.

## Machines tested
* **[1]** macOS - Mojave 10.14.6 - MacBook Pro (15-inch, 2019) - 2.3 GHz Intel Core i9 - Radeon Pro 560X 4 GB GPU
* **[2]** Ubuntu - 18.04.2 LTS x86_64 - Intel i7-8565U (x) @ 4.5GHz - NO GPU
* **[3]** Windows 10 - Intel(R) Core i7-7700HQ 2.8GHz - NO GPU 
* **[4]** Windows 10 - Intel(R) Xeon(R) CPU E5-2643 v3 3.4GHz - NVIDIA GeForce GTX 1080 Ti

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
| Test | Machine | GPU | # actors | # vertices | FPS* | run duration | benchmark file |
| ---- |:-------:|:---:|:--------:|:----------:|:---:|:------------:| --------------:|
| 10k cells | [1] | yes | 3 | 1029324 | 24.76 | 0.81s | bm_cells.py |
|  | [2] | No | 3 | 1029324 | 22.46 | 1.16s | bm_cells.py |
|  | [3] | No | 3 | 1029324 | 20.00 | 1.41s | bm_cells.py |
|  | [4] | Yes | 3 | 1029324 | 100.00 | 1.34s | bm_cells.py |
| 100k cells | [1] | yes | 3 | 9849324 | 18.87 | 3.23s | bm_cells.py |
|  | [2] | No | 3 | 9849324 | 14.91 | 4.34s | bm_cells.py |
|  | [3] | No | 3 | 9849324 | 0.43 | 7.94s | bm_cells.py |
|  | [4] | Yes | 3 | 9849324 | 1.20 | 1.13s | bm_cells.py |
| 1M cells | [1] | yes | 3 | 98049324 | 2.65 | 31.01s | bm_cells.py |
|  | [2] | No | 3 | 98049324 | 2.55 | 96.49s | bm_cells.py |
|  | [3] | No | 3 | 98049324 | 0.03 | 86.75s | bm_cells.py |
|  | [4] | Yes | 3 | 98049324 | 0.13 | 36.57s | bm_cells.py |
| Slicing 10k cells | [1] | yes | 3 | 237751 | 37.64 | 0.96s | bm_cells.py |
|  | [2] | No | 3 | 237751 | 39.10 | 1.25s | bm_cells.py |
|  | [3] | No | 3 | 237751 | 26.32 | 1.88s | bm_cells.py |
|  | [4] | Yes | 3 | 237751 | 200.00| 1.34s | bm_cells.py |
| Slicing 100k cells | [1] | yes | 3 | 276092 | 31.79 | 7.77s | bm_cells.py |
|  | [2] | No | 3 | 276092 | 25.98 | 9.09s | bm_cells.py |
|  | [3] | No | 3 | 276092 | 21.28 | 16.88s | bm_cells.py |
|  | [4] | Yes | 3 | 276092 | 111.11 | 9.65s | bm_cells.py |
| Slicing 1M cells | [1] | yes | 3 | 275069 | 11.23 | 91.31s | bm_cells.py |
|  | [2] | No | 3 | 275069 | 5.39 | 104.79s | bm_cells.py |
|  | [3] | No | 3 | 275069 | 5.03 | 158.99s | bm_cells.py |
|  | [4] | Yes | 3 | 275069 | 37.04 | 97.43s | bm_cells.py |
| brain regions | [1] | yes | 1678 | 1864388 | 9.38 | 11.78s | bm_brain_regions.py |
|  | [2] | No | 1678 | 1864388 | 7.61 | 27.40s | bm_brain_regions.py |
|  | [3] | No | 1678 | 1864388 | 6.49 | 46.79s | bm_brain_regions.py |
|  | [4] | Yes | 1678 | 1864388 | 11.90 | 35.83s | bm_brain_regions.py |
| animation | [1] | yes | 8 | 96615 | 9.91 | 18.98s | bm_animation.py |
|  | [2] | No | 8 | 96615 | 22.12 | 12.63s | bm_animation.py |
|  | [3] | No | 8 | 96615 | 15.15 | 11.92s | bm_animation.py |
|  | [4] | Yes | 8 | 96615 | 47.62 | 12.29s | bm_animation.py |
| volume | [1] | yes | 12 | 49324 | 1.79 | 2.31s | bm_volume.py |
|  | [2] | No | 12 | 49324 | 1.66 | 1.95s | bm_volume.py |
|  | [3] | No | 12 | 49324 | 3.55 | 2.15s | bm_volume.py |
|  | [4] | Yes | 12 | 49324 | 23.26 | 1.21s | bm_volume.py |
* the FPS measured are approximate and are meant only as an indication of the expected performance.

Note: Volume actors don't have a number of "vertices" so are not counted heres

Note: these tests are designed to push brainrender to the limits, in practice several steps can be taken to speed up rendering times
and increase FPS. This includes decimating/smoothing Actors to reduce the number of vertices or creating meshes with lower resolution to
begin with. For most cases a significant increase in performance can be achieved with no noticeable loss in rendering quality.
For instance on computer [4] lowering the resolution of the Points actor from 8 to 4 when rendering 1M points tripled the FPS.

