# Brainrender

[![Python Version](https://img.shields.io/pypi/pyversions/brainrender.svg)](https://pypi.org/project/brainrender)
[![PyPI](https://img.shields.io/pypi/v/brainrender.svg)](https://pypi.org/project/brainrender)
[![tests](https://github.com/brainglobe/brainrender/workflows/tests/badge.svg)](https://github.com/brainglobe/brainrender/actions)
[![codecov](https://codecov.io/gh/brainglobe/brainrender/graph/badge.svg)](https://codecov.io/gh/brainglobe/brainrender)

**`brainrender` is a python package for the visualization of three dimensional neuro-anatomical data. It can be used to render data from publicly available data set (e.g. Allen Brain atlas) as well as user generated experimental data. The goal of brainrender is to facilitate the exploration and dissemination of neuro-anatomical data by providing a user-friendly platform to create high-quality 3D renderings.**

&nbsp;
&nbsp;

![Example gallery](https://iiif.elifesciences.org/lax/65751%2Felife-65751-fig3-v3.tif/full/,1500/0/default.jpg)

From: Claudi et al. (2021) Visualizing anatomically registered data with brainrender. eLife


## Documentation

`brainrender` is a project of the BrainGlobe Initiative, which is a collaborative effort to develop a suite of Python-based software tools for computational neuroanatomy. A comprehensive online documentation for brainrender can be found on the BrainGlobe website [here](https://brainglobe.info/documentation/brainrender/index.html).

Furthermore, a open-access journal article describing `brainrender` has been published in eLife, available [here](https://doi.org/10.7554/eLife.65751).


## Installation

From PyPI:

```
pip install brainrender
```

If you encounter any issues, please consult our troubleshooting guide [here](https://brainglobe.info/documentation/brainrender/installation.html):


## Quickstart

``` python
from brainrender import Scene
from brainrender.actors import Neuron

# Display the Allen Brain mouse atlas.
scene = Scene(atlas_name="allen_mouse_25um")

# Highlight the cerebral cortex.
scene.add_brain_region("CTX", alpha=0.2, color="green")

# Add a neuron morphological reconstruction,
# with coordinates pre-registered to the Allen Brain Atlas.
neuron = Neuron("/path/to/neuron/morphology.swc")
scene.add(neuron)

# Display the figure.
scene.render()

# Export to PNG.
scene.screenshot("figure.png")

# Export to HTML
scene.screenshot("figure.html")

```

## Citing `brainrender`

If you use `brainrender` in your scientific work, please cite:
```
Claudi, F., Tyson, A. L., Petrucco, L., Margrie, T.W., Portugues, R.,  Branco, T. (2021) "Visualizing anatomically registered data with Brainrender&quot; <i>eLife</i> 2021;10:e65751 [doi.org/10.7554/eLife.65751](https://doi.org/10.7554/eLife.65751)
```

BibTeX:

``` bibtex
@article{Claudi2021,
author = {Claudi, Federico and Tyson, Adam L. and Petrucco, Luigi and Margrie, Troy W. and Portugues, Ruben and Branco, Tiago},
doi = {10.7554/eLife.65751},
issn = {2050084X},
journal = {eLife},
pages = {1--16},
pmid = {33739286},
title = {{Visualizing anatomically registered data with brainrender}},
volume = {10},
year = {2021}
}

```

## Contributing

Contributions to brainrender are more than welcome. Please see the [developers guide](https://brainglobe.info/community/developers/index.html). Note that some tests are only run locally, by specifying `--runslow --runlocal` in `pytest`.
