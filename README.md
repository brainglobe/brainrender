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

To create the render BrainRender relies on [vtkplotter](https://vtkplotter.embl.es) [see [github repo](https://github.com/marcomusy/vtkPlotter)].

Check the [user guide](../blob/master/LICENSE) and the [examples](Examples) for more information


In the future I aim to include support for VR applications, if you are interested in collaborating
in this (or any other) aspect of the brain render project please get in touch.


### Mouse Light neurons morphology rendering
![a neuron](Screenshots/neuron.png?raw=true "Mouse Light"){:height="50%" width="50%"}


### Janelia mouse connectome projection data rendering
![anatomical projections](Screenshots/tractography.png?raw=true "Connectivty"){:height="50%" width="50%"}


### Reference
If you found BrainRender useful and decided to include a rendering in your talks, posters
or article, please aknowledge BrainRender's contribution.
