Brainrender supports the creation of simple videos with animations of your scene. 

This is done by using the class `BasicVideoMaker` in from `brainrender.animation.video`.
You can find an example on videomaking [here](https://github.com/BrancoLab/BrainRender/blob/master/Examples/basic_video_maker.py), or read below for more details. 

The first step for making a video is to have a brainrender scene, so let's make one:

```
import brainrender
from brainrender.scene import Scene


scene = Scene(display_inset=False, camera="sagittal")
scene.add_brain_regions(['MOs'])
```

Okay now, import `BasicVideoMaker` and make a video maker instance:

```
from brainrender.animation.video import BasicVideoMaker 
vmkr = BasicVideoMaker(scene)
```

note: the video maker takes our scene as argument. 



Creating a video is just a matter of calling `vmkr.make_video`.
When doing so, you can pass arguments to specify the folder where the video is saved, the name of the video, 
the FPS or duration of output, the number of animation steps and other paramters that speify how the scene will be animated in the video. 

Animating the scene in `BasicVideoMaker` involves rotating the camera, thus changing the position of the point of view relative to the scene. 
This is done stepwise, by rotating by a fixed ammount at each frame. 
You can specify how much you want to rotate at each frame using the `make_video` arguments `azimuth, roll, elevation`. 
The total ammount of rotation will depend on the frame-by-frame rotation and the number of frames (specified with `niters`). 

Note that you can specify the number of frames (`niters`), the `fps` and the `duration`. However if you specify both `duration` and `fps`, 
the `fps` argument is ignored as the actual `fps` is computed given the number of frames and the video duration .

To make a video where the scene makes a full turn in 30 seconds:
```
vmkr.make_video(azimuth=1, niters=360, duration=30, save_name="rotation")
```
