
# Brainrender
<p align="center">
  <img width="600" src="https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/humanbrainexp.png">
</p>

**!! NOTE: you're looking at brainrender v2.0**
We have recently released a new version of `brainrender`, version 2.0 (:tada:). This consists of an entire re-writing of the whole library to make the code cleaner, more compact. easier to read and easier to use.
We've also included a new GUI packaged with `brainrender`.
However, this does mean that code written to work with previous versions of `brainrender` will need to be adjusted slightly to wrok with the newer versions.
Main things to change:
- `scene.add_brain_regions` is now called `scene.add_brain_region` (no `s`)
- `scene.add_from_file`, `scene.add_actor`, `scene.add_sphere`... don't exist, you can just use `scene.add` to add anything to the scene.
- `scene.add_cells` and `scene.add_from_file` don't exist, the workflow is a bit different now (see examples)
- `scene.add_neurons` doesn't exist, the workflow is a bit different now (see examples)
- `scene.add_streamlines` doesn't exist, the workflow is a bit different now (see examples)
  
Everything else should be more or less the same!

**`brainrender` is a python package for the visualization of three dimensional neuro-anatomical data. It can be used to render data from publicly available data set (e.g. Allen Brain atlas) as well as user generated experimental data. The goal of brainrender is to facilitate the exploration and dissemination of neuro-anatomical data by providing a user-friendly platform to create high-quality 3D renderings.**

## Docs
:books: [brainrender docs](https://docs.brainrender.info/).
:paper: [brainrender paper](URL TO UPDATE ONCE PUBLISHED)

## Installation
You can [install `brainrender`](https://docs.brainrender.info/installation/installation) with:

```
pip install brainrender
``` 

## Citing brainrender
If you use `brainrender` in your work, please cite:
```
  CITATION TO BE UPDATED
```

## Examples
The following images were created for the publication of the [brainrender paper](URL TO UPDATE ONCE PUBLISHED). References to the original data being visualised can also be found in the paper, and the code to generate these figures can be found at [URL TO BE UPDATED]()

<img src='imgs/cellfinder_cells_3.png' width=800 style='margin:auto'></img>
<img src='imgs/gene_expression.png' width=800 style='margin:auto'></img>
<img src='imgs/human_regions.png' width=800 style='margin:auto'></img>
<img src='imgs/injection_2.png' width=800 style='margin:auto'></img>
<img src='imgs/mouse_neurons_2.png' width=800 style='margin:auto'></img>
<img src='imgs/probes.png' width=800 style='margin:auto'></img>
<img src='imgs/zfish_functional_clusters_2.png' width=800 style='margin:auto'></img>
<img src='imgs/zfish_neurons.png' width=800 style='margin:auto'></img>
<img src='imgs/zfish_regions.png' width=800 style='margin:auto'></img>
