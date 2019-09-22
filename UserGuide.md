# UserGuide

BrainRender allows users to easily interface with the Allen Reference Atlas
and Mouse Connectivty APIs to render three dimensional anatomical data. 
In addition, it supports the rendering of neuronal morphological reconstructions
of datasets downloaded from Janelia's Mouse Light project. 


## Process
### Create your scene

To create a rendering, BrainRender uses vtkplotter to create a "scene" which can
then be populated with "actors" (e.g. 3D brain regions data). The
scene is then rendered for the user to see and interact with, or used to create a video. 

Most of the process therefore relies on the `Scene` class. This class
let's users add brain regions to the rendering [see example: [[regions]](Examples/Regions.ipynb)], but it also takes care of adding tractography and neuron morphology data to the scene before rendering it. 

To see how to crate your first scene, check out the [[tutorial]](Examples/tutorial.ipynb)

### Add neuron morphology data
To add 3D neuronal morphological data to a scene, users have to first download the data
from Janelia's Mouse Light [neurons browser](http://ml-neuronbrowser.janelia.org). 
From the neurons browser, select the neurons you are interested in and download the data
as a JSON file. The downloaded data can then be used to recreate the neurons in the renderings. 

Users can combine morphological renderings with the display of brain regions of interested
in the same scene to get a better understanding of the projection targets of the neurons 
that users are interested in. 

To see how to add neurons to a scene, check out the tutorial on [[neurons]](Examples/Neurons.ipynb)

### Add tractography data 
The Allen Brain Atlas Mouse Connectivty project collected data from a large number 
of experiments in which viral tracers were injected into wild type and CRE driver lines
to investigate anatomical projections between brain regions. 
To get these data Allen provides an API, and BrainRender uses this API to fetch
anatomical projection data and render these projections in 3D as part of a scene. 

The interaction with the API is mediated by the class `ABA` which let's users 
fetch tractography data to reconstruct projections to a brain region of interest. 

Tractography data can be displayed in combination with brain region anatomical data 
and neurons reconstruction data. To see how this works, have a look at the 
example on [[tractography]](Examples/Tractography.ipynb)

### Make video
`Scene` let's users create and display interactive 3D rendererings which can be used 
inspect anatomical data and grab screenshots. To create an animated video of your 
scene to enbed in talks and website you can use the `VideoMaker` class, as shown in 
the example on [[making videos]](Examples/Videos.ipynb)

In the future BrainRender will also allow users to export their scenes so that they can 
be enbed into a web page. 