# Installation
To use `brainrender` you will need a python enviornment with `python < 3.8`. If you don't have one, please [create it now](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)

Once you have an environment in place, simply install `brainrender` with:
```
pip install brainrender
```

If you want to get the latest version of `brainrender` before it gets updated on pip, you get get it with:
```
https://github.com/BrancoLab/BrainRender.git
```

If you want to get the example files, or would like to edit the code, the easiest way is to clone/fork this repository on your machine and take it from there.


# Usage
Brainrender's core element is the `Scene` class, this takes care of downloading some of the data and rendering all of it. Other classes are needed to download some of the data, read below for details.
A `brainrender` `scene` is populated with 'actors' representing items to be rendered. 

You can use `Scene` to:
  1) Download/render the 3D anatomy of brain regions from the Allen atlas
  2) Render mesoscale connectomics data (tractography and streamlines)
  3) Render neuronal morphologies from Janelia's MouseLight project
  4) Render the location of labelled cells
  5) Render other objects such as implanted electrodes. 

Rendering of actors in `brainrender` is very flexible, you can specify how almost every aspect of any actor should look like. This can be done by passing the appropriate arguments to the functions used to add actors to a scene. You can also specify default values for these parameters. Have a look at `brainrender.default_variables` to see what the available parameters are. You can edit the default parameters by editing the `config.yaml` file in the `.brainrender` folder that hosts all data downloaded by brainrender (`.brainrender` is saved in your Home or Use folder).


## Adding brain regions to a Scene.
The `scene` class interacts with the API (Application Programming Interface) and SDK (Software Development Kit) from the Allen institute to download data from Allen's projects. To make the process of populating a scene as straightforward as possible, `brainrender` handles interaction with these services behind the scenes, all you have to do is to specify which brain regions you want to add your scene. **In `brainrender` regions from the Allen atlas are identified by their acronym**. If you are unsure about what the acronym of your region of interest is, have a look [here](../mouse_regions.txt). 

Adding a brain region to a scene is as simple as this:
```
  from brainrender.scene import Scene
  scene = Scene()
  scene.add_brain_regions(['MOs', 'VISp'])
```

## Adding mesoscale connectomics.
### Afferent projections
To download afferent projections, visualised as tractography, you'll need the `ABA` class. 
`ABA` takes care of most interactions with the Allen Brain Atlas, including downloading tractography data.
Once you've downloaded the data, use `Scene` to render it.


```
from brainrender.scene import Scene
from brainrender.Utils.ABA.connectome import ABA

scene = Scene()
aba = ABA()

tract = aba.get_projection_tracts_to_target("CA1") 
scene.add_tractography(tract, color_by="region")
```

### Efferent projections
You can visualise efferent projections from a region of interest as *streamlines*. 
To do this, first you need to download relevant streamlines data from [neuroinformatics.nl](https://neuroinformatics.nl) using the `StreamlinesAPI`. Downloaded data, can then be rendered with `Scene`.

```
from brainrender.scene import Scene
from brainrender.Utils.ABA.connectome import ABA

scene = Scene()
streamlines_api = StreamlinesAPI()

streamlines_files, data = streamlines_api.download_streamlines_for_region("RE") 
scene.add_streamlines(data)
```


## Neuronal morphology
Brainrender can be used to visualise neuronal morphologies downloaded from the MouseLight project and from any `.swc` file. 

You could download the data for the neurons you are interested in from the MouseLight website, but you can also do so in brainrender, using the `MouseLightAPI` class.

```
from brainrender.scene import Scene
from brainrender.Utils.MouseLightAPI.mouselight_info import mouselight_api_info, mouselight_fetch_neurons_metadata
from brainrender.Utils.MouseLightAPI.mouselight_api import MouseLightAPI

mlapi = MouseLightAPI()
scene = Scene()

neurons_metadata = mouselight_fetch_neurons_metadata(filterby='soma', filter_regions=['MOp5'])
neurons_files =  mlapi.download_neurons(neurons_metadata[0]) 
scene.add_neurons(neurons_files)
```

You can visualise neuronal morphologies even if they are not registered to Allen atlas (e.g. data downloaded from [neuromorpho](www.neuromorpho.org)).
Just make sure to disable the rendering of the 'root' brain actor when instantiating the scene:

```
  scene = Scene(add_root=False)
```

## Visualising labelled cells
If you have the location of lablled cells saved as a `.h5` file or `pandas.DataFrame` you can use scene to render them. Just use the `Scene.add_cells()` function. 

## Visualising other kinds of data
You can use `brainrender` to visualise almost anything (thanks to the awesome `vtkplotter` that brainrender depends upon). You can load `.obj` and `.stl` files and render them directly in your `Scene`. 
The `Scene` class can also be used to render simple shapes (e.g. a cylinder to represent an optic fibre) directly, with `Scene.add_optic_cannula()`.

## Making videos, taking photos.
You can take screenshows of a rendered scene simply by pressing `s` while interacting with the scene. 
There's also a `VideoMaker` class to make simple animations, head over to the Examples to see how to use this.


# Contributing
Contributions are welcomed! Feel free to open an issue or send an email for bug reports, feature requests, questions or any kind of contribution.

