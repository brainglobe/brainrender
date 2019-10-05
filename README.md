### Disclaimer
BrainRender is a fairly new project and therefore incomplete and bound to include bugs.
If you find a bug, or spot a feature that you'd like to see added, please open an issue
and I'll get to work on it as soon as possible. 

# BrainRender
Python scripts to create 3D renderings of mouse brain anatomical and projection data and neurons reconstructions. 

Anatomical and projection data is downloaded from the  Allen Brain Atlas [reference atlas](http://atlas.brain-map.org)
and [connectivity atlas](http://connectivity.brain-map.org) using the Allen [API](http://help.brain-map.org/display/api/Allen%2BBrain%2BAtlas%2BAPI). 

Neurons morphological data is from Janelia's [mouse light](https://www.janelia.org/project-team/mouselight)
(see the [neurons browser](http://ml-neuronbrowser.janelia.org)). 

Streamlines reconstructions are made by [https://neuroinformatics.nl](https://neuroinformatics.nl) using the mouse connectome data from allen (see [here](https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html) for more details)

BrainRender also includes meshes for a reconstruction of the rat brain. These meshes are obtained and modified from  
[3D-rat-brain](https://github.com/tfiers/3D-rat-brain) from 
[tfiers](https://github.com/tfiers). 

To create the render BrainRender relies on [vtkplotter](https://vtkplotter.embl.es) [see [github repo](https://github.com/marcomusy/vtkPlotter)].

Check the [user guide](UserGuide.md) and the [examples](Examples) for more information


In the future I aim to include support for VR applications, if you are interested in collaborating
in this (or any other) aspect of the brain render project please get in touch.


## Mouse Light neurons morphology rendering
<img src="Screenshots/neuron.png" width="600" height="350">
Motor cortex piramidal neuron reconstruction from Mouse Light.

## Rendering of different sets of brainstem projecting neurons using MultiScene
<img src="Screenshots/multiscene_1.png" width="600" height="350">
Sets of neurons projecting to the brainstem, sorted by brain region.

## Allen mouse connectome projection data rendering
### Tractography
<img src="Screenshots/tractography.png" width="600" height="350">
Projections to the Zona Incerta, colored by projection area.

### Streamlines
<img src="Screenshots/streamlines2.png" width="600" height="350">
Efferents from the VAL nucleus of the thalamus.

### Streamlines
<img src="Screenshots/streamlines2.png" width="600" height="350">
Efferents from the VAL nucleus of the thalamus.

### Ratbrain
<img src="Screenshots/ratbrain2.png" width="600" height="350">
The rat and mouse brains side by side. 


### Reference
If you found BrainRender useful and decided to include a rendering in your talks, posters or article, please aknowledge BrainRender's contribution.
