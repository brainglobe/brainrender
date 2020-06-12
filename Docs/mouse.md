# Description
## Publicly available datasets
One of the main goal of `brainrender` is to provide a single platform to explore anatomical data from many
publicly available datasets. Below is a quick description of some of the things that `brainrender` can be used for when working with data from the mouse brain. 

## Allen Mouse Brain Atlas and Mouse Connectome Project
Anatomical and projection data is downloaded from the  Allen Brain Atlas [reference atlas](http://atlas.brain-map.org)
and [connectivity atlas](http://connectivity.brain-map.org) using the Allen [API](http://help.brain-map.org/display/api/Allen%2BBrain%2BAtlas%2BAPI)
(© 2015 Allen Institute for Brain Science. Allen Brain Atlas API. Available from: [https://brain-map.org/api/index.html](https://brain-map.org/api/index.html)) ([1], [2]).


### Brain structures
Brain structures are the most fundamental element of any `brainrender` scene. You can use brainrender to select which brain regions you'd like to visualise, and how they should look (color, transparency...). Brainrender then takes care of downloading and rendering the 3D mesh for the selected regions. 




### Efferent projections (Streamlines)
Efferent anatomical projections  from a region of interest as determined by local injections of an anterogradely transported virus (see [Allen's connectivity atlas](http://connectivity.brain-map.org)) can be rendered as 'streamlines'.

Streamlines reconstructions are made by [https://neuroinformatics.nl](https://neuroinformatics.nl) using the mouse connectome data from Allen (see [here](https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html) for more details). 
Brainrender automatically downloads and renders streamlines data for a brain region of interest. 



Brain structures             |  Afferent projections
:-------------------------:|:-------------------------:
![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/brainregions.png)  |  ![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/tractography.png)

Efferent projections             |  Gene Expression
:-------------------------:|:-------------------------:
![](https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/streamlines.png)  | <img src="Docs/Media/clean_screenshots/gene_expr.png">


### Afferent projections (tractography)
The same data used to extract information about efferent projections, can be visualised in an alternative way to look at afferent projections to a region of interest. In `brainrender` this type of data visualisation is called tractography. 
Brainrender can be used to select the subset of experiment (injection of an anterograde virus expressing a fluorescent marker) which resulted in fluorescence in the region of interest from the >1000 experiments in the Allen Mouse Connectome project. 
The location of virus injection and the projection from that location to the region of interest is then displayed. 


### Gene expression data.
The Allen [brain atlas](http://mouse.brain-map.org/) includes a dataset of volumetric gene expression across the entire mouse brain. Brainrender can be used to [download](http://help.brain-map.org/display/api/Downloading+3-D+Expression+Grid+Data) and visualize this kind of data.


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


<img src="https://github.com/BrancoLab/BrainREnder/raw/master/Docs/Media/morphology.png" width="700">


