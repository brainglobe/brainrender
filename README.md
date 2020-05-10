
# BrainRender
<img src="https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/humanbrainexp.png" width="700">


`brainrender` is a python package for the visualization of three dimensional neuroanatomical from publicly available dataset (e.g. Allen Brain atlas) and from user generated experimental data. 
The goal of brainrender is to faciliate the exploration and communication of neuroanatomical data by providing a user-friendly
platform to create 3D renderings. 


For more information about `brainrender` and how to use it, checkout the [brainrender preprint](https://www.biorxiv.org/content/10.1101/2020.02.23.961748v1).
You can find interactive examples of data visualisations generated with brainrender [here](https://fedeclaudi.github.io/br-info.html) and a gallery of images created with brainrender [here](https://fedeclaudi.github.io/br-gallery.html)

<img src="https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/neurons_transparent.png" width="700">

# Installation
To install `brainrender`, use an existing python environment or [create](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) one [with `python < 3.8`] and install with:
```
pip install brainrender
```


# Description
## Publicly available datasets
One of the main goal of `brainrender` is to provide a single platform to explore anatomical data from many
publicly available datasets. Given that `brainrender` was initially developed for working on mouse data, most 
features involve datasets of anatomical data for the mouse brain.  Here's a quick description of some of the things that `brainrender` can be used for. 

## Allen Mouse Brain Atlas
Anatomical and projection data is downloaded from the  Allen Brain Atlas [reference atlas](http://atlas.brain-map.org)
and [connectivity atlas](http://connectivity.brain-map.org) using the Allen [API](http://help.brain-map.org/display/api/Allen%2BBrain%2BAtlas%2BAPI)
(© 2015 Allen Institute for Brain Science. Allen Brain Atlas API. Available from: [brain-map.org/api/index.html](brain-map.org/api/index.html)) ([1], [2]).

### Brain structures
Brain structures are the most fundamental element of any `brainrender` scene. You can use brainrender to select which brain regions you'd like to visualise, and how they should look (color, transparency...). Brainrender then takes care of downloading and rendering the 3D mesh for the selected regions. 

[example: [brain_regions.py](Examples/mouse/brain_regions.py)]



### Efferent projections (Streamlines)
Efferent anatomical projections  from a region of interest as determined by local injections of an anterogradely transported virus (see [Allen's connectivity atlas](http://connectivity.brain-map.org)) can be rendered as 'streamlines'.

Streamlines reconstructions are made by [https://neuroinformatics.nl](https://neuroinformatics.nl) using the mouse connectome data from Allen (see [here](https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html) for more details). 
Brainrender automatically downloads and renders streamlines data for a brain region of interest. 

[example: [streamlines.py](Examples/mouse/streamlines.py)]


Brain structures             |  Afferent projections
:-------------------------:|:-------------------------:
![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/brainregions.png)  |  ![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/tractography.png)

Efferent projections             |  MouseLight neurons
:-------------------------:|:-------------------------:
![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/streamlines.png)  |  ![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/morphology.png)

### Afferent projections (tractography)
The same data used to extract information about efferent projections, can be visualised in an alternative way to look at afferent projections to a region of interest. In `brainrender` this type of data visualisation is called tractography. 
Brainrender can be used to select the subset of experiment (injection of an anterograde virus expressing a fluorescent marker) which resulted in fluorescence in the region of interest from the >1000 experiments in the Allen Mouse Connectome project. 
The location of virus injection and the projection from that location to the region of interest is then displayed. 

[example: [tractography.py](Examples/mouse/tractography.py)]



### Volumetric projections
Brainrender can now use the model from [4] to visualise projection spatialised projections from one (or more) source brain region to one (or more) target brain region. By that we mean that you can see where in the target brainregion you have the strongest projections from the source region, as shown in this example:

MOs to STR             |  SSs to STR          |   SSp to STR
:-------------------------:|:-------------------------:|:-------------------------:
![](https://raw.githubusercontent.com/BrancoLab/BrainREnder/master/Docs/Media/MOs_to_STR_mean_20200305_165259.png)|  ![](https://raw.githubusercontent.com/BrancoLab/BrainREnder/master/Docs/Media/SSs_to_STR_mean_20200305_165302.png)| ![](https://raw.githubusercontent.com/BrancoLab/BrainREnder/master/Docs/Media/SSp_to_STR_mean_20200305_165304.png) 



## Mouselight neuronal reconstructions
`Brainrender` can be used to download and render
neurons morphological data from Janelia's [mouse light](https://www.janelia.org/project-team/mouselight) database
(see the [neurons browser](http://ml-neuronbrowser.janelia.org)). [3]
These reconstructions are aligned to the Allen brain atlas, so the neurons morphology can be visualised along other types of data (e.g. efferent/afferent projections) in `brainrender`.

[example: [mouselight.py](Examples/mouse/mouselight.py)]

<img src="https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/morphology.png" width="700">



## User generated content
Brainrender can be used to visualise data generated within individual labs, such as the results of a tracing experiments. 



Injection site             |  Labelled neurons
:-------------------------:|:-------------------------:
![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/inj_site.png)  |  ![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/labelled_cells.png)

This often requires that the raw data be registered to the Allen atlas (or any other atlas supported by brainrender), before being visualised.
This functionality is not supported in `brainrender`, however brainrender can be used to visualise data registered with other packages such as `amap` ([github repo](https://github.com/SainsburyWellcomeCentre/amap-python)) and `cellfinder` ([github repo](https://github.com/SainsburyWellcomeCentre/cellfinder)).


You can also use `brainrender` to visualise the position of devices implanted in the brain (e.g. optic cannula). 
This can only be done by rendering colored cylinders at the location where the implant is or by loading in 3d 
rendering of the implanted devices from .obj or .stl files.


Optic fibre             |  Electrodes array         |  Neuropixel Probe
:-------------------------:|:-------------------------:|:-------------------------:
![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/cannula.png)  |  ![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/electrodes.png) |  <img src="https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/sharp_track_probe.png" width="1900">

Thanks to @tbslv's contribution brainrender can be integrated with SharpTrack from the Cortex Lab [https://github.com/cortex-lab/allenCCF] to visualise the location of implanted neuropixel probes. 




## Making figures
Brainrender's high quality renderings can be exported as `.png` images directly within brainrender.
Brainrender's flexibility when it comes to specify the appearance of rendered objects means that it can easily be used to display data as well as create schematics for scientific publications. 

Optic fibre             |  Electrodes array         |  Neuropixel Probe
:-------------------------:|:-------------------------:|:-------------------------:
<img src="https://github.com/BrancoLab/BrainREnder/raw/masterDocs/Media/skull.png" width="1900">  |  <img src="https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/streamlinespretty.png" width="1900"> |  <img src="https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/aba.png" width="1900">




Brainrender can also be used to create videos and animations, check out the examples to see how you can create videos from within brainrender.


MouseLight neuron             |  Labelled cells
:-------------------------:|:-------------------------:
![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/neuron_gif.gif) |  ![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/cells.gif)




# Behind the scenes
Brainrender was deisgned to be a powerful and flexible software for downloading and rendering neuroanatomical data while still being relatively easy to use (using brainrender requires minimal coding experience). 
This was achieved by: 
  1) handling the interaction with the API, SDK and databases services used to find and download the data behind the scenes, requiring minimal user input. 
  2) Using [vtkplotter](https://vtkplotter.embl.es) to handle the rendering. Vtkplotter  ([github repo](https://github.com/marcomusy/vtkPlotter)) is a powerful rendering engine that produces high quality three dimensional rendering. Vtkplotter is also flexible, meaning that it can handle data provided in various file formats, allowing `brainrender` to render data from various sources. 

# Getting in touch
If you're unsure how to use `brainrender`, please start by having a look at the  [user guide](https://github.com/BrancoLab/BrainRender/blob/master/Docs/UserGuide.md) and the [examples](https://github.com/BrancoLab/BrainRender/blob/master/Examples) notebooks. If you still have unanswered questions, please do not hesitate to get in touch (the easiest way is to open an issue on github). 

For any bug report or feature request, please open an issue with a brief description of the matter. 
Although brainrender can already to much, we are always happy to add more functionality that could be useful for users. If you spot some feature that is missing, we'd love to hear about is so please get in touch!

## Referencing Brain Render
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


## References
* [1] Lein, E.S. et al. (2007) Genome-wide atlas of gene expression in the adult mouse brain, Nature 445: 168-176. doi:10.1038/nature05453
* [2] Oh, S.W. et al. (2014) A mesoscale connectome of the mouse brain, Nature 508: 207-214. doi:10.1038/nature13186
* [3]  Winnubst, J. et al. (2019) Reconstruction of 1,000 Projection Neurons Reveals New Cell Types and Organization of Long-Range Connectivity in the Mouse Brain, Cell 179: 268-281
* [4] Knowx et al (2018). High-resolution data-driven model of the mouse connectome.
