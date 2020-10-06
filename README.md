
# Brainrender
<p align="center">
  <img width="600" src="https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/humanbrainexp.png">
</p>


**`brainrender` is a python package for the visualization of three dimensional neuro-anatomical data. It can be used to render data from publicly available data set (e.g. Allen Brain atlas) as well as user generated experimental data. The goal of brainrender is to facilitate the exploration and dissemination of neuro-anatomical data by providing a user-friendly platform to create high-quality 3D renderings.**

This page is meant as a brief overview of `brainrender`'s functionality. For more detailed information about how to install and use `brainrender` please visit check the [brainrender docs](https://docs.brainrender.info/).




# Installation
You can [install `brainrender`](https://docs.brainrender.info/installation/installation) with:

```
pip install brainrender
``` 


To quickly check that everything worked for your installation, try creating a brainrender scene directly from the terminal. 
```
  brainrender TH STR -c
```

## Graphic User Interface
While brainrender doesn't come with a GUI, one is being developed by BrainGlobe. If you follow the link you will find instructions on how to install and use [brainglobe's brainrender GUI](https://github.com/brainglobe/bg-brainrender-gui) for creating a scene and adding elements to it. 


---------
----
# Usage
`brainrender` relies on brainglobe's [brainatlas-api](https://github.com/brainglobe/brainatlas-api) to fetch structural and morphological data for various brain atlases, including two mice atlases, one zebrafish atlas and one atlas of the human brain. Much of what brainrender can do works across all of these atlases. 

Basic functionality supported by `brainrender` includes the display of anatomical brain regions, the position of labelled cells (e.g. as obtained with tools like [cellfinder](https://github.com/SainsburyWellcomeCentre/cellfinder)) and whole-cell neuronal morphological reconstructions. Click on the images below to see aexamples  of how to use brainrender:



Brain structures             |  Labelled cells        |  Neuron reconstructions
:-------------------------:|:-------------------------:|:-------------------------:
<a href="Examples/basic/brain_regions.py" target="_blank"><img src="Docs/Media/clean_screenshots/regions.png"><br>`brain_regions.py` </a>| <a href="Examples/basic/labelled_cells2.py" target="_blank"><img src="Docs/Media/clean_screenshots/cells.png"><br>`labelled_cells2.py`</a> |  <a href="Examples/mouse/colored_neurons.py" target="_blank"><img  src="Docs/Media/clean_screenshots/neurons2.png"><br>`colored_neurons.py`</a>




## Mouse brain-specific
Some of brainrenders functionality is specific to the atlases based on the Allen mouse brain atlas. This includes functionality to render publicly available as well as user-generated data.

### Publicly available datasets
Brainrender can be used to download a visualize a neuroanatomical data from several publicly available datasets based on the Allen Atlas of the mouse brain.
Anatomical and projection data is downloaded from the  Allen Brain Atlas [reference atlas](http://atlas.brain-map.org)
and [connectivity atlas](http://connectivity.brain-map.org) using the Allen [API](http://help.brain-map.org/display/api/Allen%2BBrain%2BAtlas%2BAPI)
(© 2015 Allen Institute for Brain Science. Allen Brain Atlas API. Available from: [https://brain-map.org/api/index.html](https://brain-map.org/api/index.html)) ([1], [2]). Brainrender can also be used to download and visualise gene expression data from the Allen database and
neurons morphological data from Janelia's [mouse light](https://www.janelia.org/project-team/mouselight) project
(see the [neurons browser](http://ml-neuronbrowser.janelia.org)). [3]


Streamlines             |  Tractography        |   
:-------------------------:|:-------------------------:|
<a href="Examples/mouse/streamlines.py" target="_blank"><img style="width:400px" src="Docs/Media/clean_screenshots/streamlines.png"><br>`streamlines.py`</a> | <a href="Examples/mouse/tractography.py" target="_blank"><img style="width:400px" src="Docs/Media/clean_screenshots/tractography.png"><br>`tractography.py` </a>


gene expression | MouseLight
:-------------------------:|:-------------------------:|
 <a href="Examples/mouse/gene_expression.py" target="_blank"><img style="width:400px" src="Docs/Media/clean_screenshots/gene_expr.png"><br>`gene_expression.py`</a> |  <a href="Examples/mouse/mouselight.py" target="_blank"><img style="width:400px" src="Docs/Media/clean_screenshots/neurons.png"><br>`mouselight.py`</a>

### User generated
`brainrender` can be used to visualise the location of implanted neuropixel probes with data from [SHARP TRACK](https://github.com/cortex-lab/allenCCF).
Neuropixel             | 
:-------------------------:|
<a href="Examples/user_data/sharptrack.py" target="_blank"><img style="width:400px" src="Docs/Media/clean_screenshots/neuropixel.png" style="width:400px"><br>`sharptrack.py` </a>| 


## Exporting
To facilitate the creation of scientific illustrations, brainrender let's you take screenshots of your scenes, create animated videos and embed [interactive visualisations](https://fedeclaudi.github.io/br-info.html) scenes in your website. 

To learn how to do it, check these examples:
 - [screenshot](Examples/export/screenshots.py)
 - [video1](Examples/export/basic_video_maker.py) - [video2](Examples/advanced/custom_videomaker.py)
 - [animation](Examples/advanced/animated_scene.py)
 - [export for web](Examples/export/export_for_web.py)


## Other
`brainrender` relies on the powerful `vedo`(https://vedo.embl.es) ([github](https://github.com/marcomusy/vedo)) rendering engine, thus providing you with the flexibility to render just about anything you might need for your visualisation. As an example, here you can see how to visualise the location of an implanted optic fiber or any other 3d object from an `.stl` or `.obj` file. 


Optic fibre             |  .stl file visualisation | .obj file visualisation
:-------------------------:|:-------------------------:|:-------------------------: 
<a href="Examples/user_data/add_optic_cannula.py" target="_blank"><img style="width:480px"  src="Docs/Media/clean_screenshots/optic_fiber.png"><br>`add_optic_cannula.py` </a>| <a href="Examples/user_data/add_object_to_scene.py" target="_blank"><img style="width:480px"  src="Docs/Media/clean_screenshots/skull.png"><br>`add_object_to_scene.py`  </a> | <a href="Examples/user_data/add_object_to_scene.py" target="_blank"><img style="min-width:200px;max-width:300px" src="Docs/Media/clean_screenshots/inj_site.png"><br>`add_object_to_scene.py`</a>



## Other atlases
In addition to the atlases supported by `brainatlas-api`, you can easily create new `Atlas` classes to support the visualisation of your own datasets in `brainrender` (see [here](Docs/custom_atlases.md) for more details). As a way of example we provide two such classes. One to visualise insect brains from [insectbraindb.org]( https://insectbraindb.org/app/) and one for _C. Elegans_ connectome data from Daniel Witvliet's recent [preprint](https://www.biorxiv.org/content/10.1101/2020.04.30.066209v1).

Insect brains             |  _C. Elegans_ connectome   
:-------------------------:|:-------------------------:
<a href="Examples/custom_atlases/insects_brains.py" target="_blank"><img  src="Docs/Media/clean_screenshots/ibdb.png"><br>`insects_brains.py` </a>| <a href="Examples/custom_atlases/celegans_connectome.py" target="_blank"><img  src="Docs/Media/clean_screenshots/celegans.png"><br>`celegans_connectome.py` </a>


# Getting in touch
If you're unsure how to use `brainrender`, please start by having a look at the [docs](https://docs.brainrender.info/) and [examples](Examples). If you still have unanswered questions, please do not hesitate to get in touch (the easiest way is to open an issue on github). 

For any bug report or feature request, please open an issue with a brief description of the matter. 
Although brainrender can already to much, we are always happy to add more functionality that could be useful for users. If you spot some feature that is missing, we'd love to hear about is so please get in touch!


## Referencing brainrender
If you found BrainRender useful and decided to include a rendering in your talks, posters or article, please acknowledge BrainRender's contribution by citing the [brainrender preprint](https://www.biorxiv.org/content/10.1101/2020.02.23.961748v1) as:
```
Brainrender. A python based software for visualisation of neuroanatomical and morphological data.
Federico Claudi, Adam L. Tyson, Tiago Branco
bioRxiv 2020.02.23.961748; doi: https://doi.org/10.1101/2020.02.23.961748 
```


# Similar tools
## In R
`cocoframer` is an R library for interacting with the Allen's Mouse CCF [github repository](https://github.com/AllenInstitute/cocoframer).

`mouselightr` package generates 3D CCF mouse brain plots, along with MouseLight neuron reconstructions [github repository](https://github.com/jefferis/nat.mouselight)

### In Matlab
`BrainMesh` is a Matlab GUI for rendering 3D mouse brain structure [github repository](https://github.com/Yaoyao-Hao/BrainMesh).


## References
* [1] Lein, E.S. et al. (2007) Genome-wide atlas of gene expression in the adult mouse brain, Nature 445: 168-176. doi:10.1038/nature05453
* [2] Oh, S.W. et al. (2014) A mesoscale connectome of the mouse brain, Nature 508: 207-214. doi:10.1038/nature13186
* [3]  Winnubst, J. et al. (2019) Reconstruction of 1,000 Projection Neurons Reveals New Cell Types and Organization of Long-Range Connectivity in the Mouse Brain, Cell 179: 268-281
* [4] Knowx et al (2018). High-resolution data-driven model of the mouse connectome. -->
