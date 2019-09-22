# BrainRender
Python scripts to create 3D renderings of mouse brain anatomical and projection data and neurons reconstructions. 

Anatomical and projection data is downloaded from the  Allen Brain Atlas [reference atlas](http://atlas.brain-map.org)
and [connectivity atlas](http://connectivity.brain-map.org) using the Allen [API](http://help.brain-map.org/display/api/Allen%2BBrain%2BAtlas%2BAPI). 

Neurons morphological data is from Janelia's [mouse light](https://www.janelia.org/project-team/mouselight)
(see the [neurons browser](http://ml-neuronbrowser.janelia.org)). 

To create the render BrainRender relies on [vtkplotter](https://vtkplotter.embl.es) [see [github repo](https://github.com/marcomusy/vtkPlotter)].

Check the [user guide](../blob/master/LICENSE) and the [examples](Examples) for more information


### Mouse Light neurons morphology rendering
![a neuron](screenshots/neuron.png?raw=true "Title")



### Janelia mouse connectome projection data rendering
![anatomical projections](screenshots/tractography.png?raw=true "Title")
