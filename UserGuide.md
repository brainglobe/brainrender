# UserGuide

BrainRender allows users to easily interface with the Allen Reference Atlas and Mouse Connectivty APIs to render three dimensional anatomical data. 
In addition, it supports the rendering of neuronal morphological reconstructions of datasets downloaded from Janelia's Mouse Light project. 


## Overview
BrainRender let's you interact with the Allen Brin Atlas API to download and visualize anatomical and projection data. 
BrainRender also let's you visualize 3d morphological reconstruction of neurons shared by the Mouse Light project at Janelia alongside the anatomical data from Allen. 
The aim of BrainRender is to make it easy to crate personalized renderings of mouse brain anatomy to let users get a better understanding of the brain regions they are working on, and to crate high quality images and videos for scientific talks, posters and publications. 

In brief, the process of creating a rendering consists of creating a 'Scene' to which 'actors' can be added before rendering. 
These 'actors' represent brain regions, neurons, tractography data etc. 
The user can select what to show in the scene and what it should look like. 


## Process
### Installation
To use BrainRender, the first thing to do is to clone this github repository on your machine, this gives you access to the code, the examples and the data stored in this repository.

You then need to set up a python environment to use BrainRender with. 
If you are using anaconda you can simply crate an environment using the installation .yml file in the [Installation](Installation) subdirectory, just use this command in you anaconda Prompt:

```conda env create --name NAME --file path_to_your_repo/Installation/environment.yml```


### Folder structure
BrainRender needs to save and access data from your machine. 
For this reason you will need to specify the folder in which each type of data will be stored [for more details please see [settings.py](BrainRender/settings.py)]. 
The easiest way to do so is to edit [settings.py](BrainRender/settings.py) to make `folders_paths['main_fld']` the directory in which you want to store the data. 
If you then run `settings.py` it will take care of creating the subfolders for you. 
Alternatively, you can change the 'main_fld' at runtime as shown in this [example](Examples/Tutorial.ipynb).


### Variables
One of the main aims of BrainRender is to let users personalize their rendering as much as possible. 
This include changing color and transparency of rendered items, coloring items according to different criteria etc. 
This is achieved in part by passing different arguments to the functions that take care of the rendering 
as shown in the [examples](Examples), but BrainRender's behaviour can also be controlled by variables defined in
[variables.py](BrainRender/variables.py). 
These variables define the default values for many parameters used for rendering, so it's definitively worth having a look at their description in [variables.py](BrainRender/variables.py) and playing around them to achieve the best results. 


### Create your scene
To create a rendering, BrainRender uses vtkplotter to create a "scene" which can then be populated with "actors" (e.g. 3D brain regions data). 
The scene is then rendered for the user to see and interact with, or used to create a video. 

Most of the process therefore relies on the `Scene` class. 
This class let's users add brain regions to the rendering (see example: [regions](Examples/Regions.ipynb)), but it also takes care of adding tractography and neuron morphology data to the scene before rendering it. 
You can find a list of all structures that can be displayed [here](all_regions.txt).

To see how to crate your first scene, check out the [tutorial](Examples/tutorial.ipynb).

### Add neuron morphology data
To add 3D neuronal morphological data to a scene, users have to first download the data from Janelia's Mouse Light [neurons browser](http://ml-neuronbrowser.janelia.org). 
From the neurons browser, select the neurons you are interested in and download the data as a JSON file. 
The downloaded data can then be used to recreate the neurons in the renderings. 

Users can combine morphological renderings with the display of brain regions of interested in the same scene to get a better understanding of the projection targets of the neurons that users are interested in. 

To see how to add neurons to a scene, check out the tutorial on [neurons](Examples/Neurons.ipynb).

### Add tractography data 
The Allen Brain Atlas Mouse Connectivty project collected data from a large number of experiments in which viral tracers were injected into wild type and CRE driver lines to investigate anatomical projections between brain regions. 
To get these data Allen provides an API, and BrainRender uses this API to fetch anatomical projection data and render these projections in 3D as part of a scene. 

The interaction with the API is mediated by the class `ABA` which let's users fetch tractography data to reconstruct projections to a brain region of interest. 

Tractography data can be displayed in combination with brain region anatomical data and neurons reconstruction data. 
To see how this works, have a look at the example on [tractography](Examples/Tractography.ipynb).

### Add streamline data
Streamlines can be used to beautifully display projection data. To render streamliens you first need to download the data for the experiments you are interested in. 
The first step towards being able to render streamlines data is to identify the set of experiments you are interested in 
(i.e. injections in the primary visual cortex of wild type mice]. 
To do so you can use the experiments explorer at [http://connectivity.brain-map.org](http://connectivity.brain-map.org).

Once you have selected the experiments, you can download metadata about them using the 'download data as csv' option at the bottom of the page. 
This metadata .csv is what we can then use to get a link to the data to download. 

These data can then be simply rendered in BrainRender, as you can see in this [example](Examples/Streamlines.ipynb).

### Scenes with multiple views
To get a better understanding of the anatomy and connectivity of a brain region it is often uesful to look at information from different sources at the same time: reconstruction of neurons in the brain region can be combined with rendering of neraby regions and tractography data for instance. 
This can make the scene cluttered. 
So it is convenient to be able to render similar variants of the same scene side by side so that differend datasets can be rendered in each variant. 
This can be done using the `DualScene` and `MultiScene` classes in brainrender. 
Their use is similar to that of `Scene`, except that they allow you to generate N scenes and specif what get's rendered in which. 
For more details have a look at the example on [MultiScene](Examples/MultiScene.ipynb).

### Make video
`Scene` let's users create and display interactive 3D renderings which can be used inspect anatomical data and grab screenshots. To create an animated video of your scene to embed in talks and website you can use the `VideoMaker` class, as shown in 
the example on [making videos](Examples/Video.ipynb).

In the future BrainRender will also allow users to export their scenes so that they can be embed into a web page. 


### Rat Brain
BrainRender also let's you visualize the rat brain! To do so simply
use the `RatScene` as you would the standard `Scene` class. It works
the same but it loads the meshes for the rat brain (from [3D-rat-brain](https://github.com/tfiers/3D-rat-brain)).
You can find an example for `RatScene` [here](Examples/RatScene.ipynb).