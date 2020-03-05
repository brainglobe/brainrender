"""
    This tutorial shows you how to render efferent mesoscale connectivity
    data from the Allen mouse connectome project as streamlines. 

"""

from brainrender.scene import Scene
from brainrender.Utils.parsers.streamlines import StreamlinesAPI

# Download streamlines data for injections in the CA1 field of the hippocampus
streamlines_api = StreamlinesAPI()
filepaths, data = streamlines_api.download_streamlines_for_region("CA1")

# Start by creating a scene
scene = Scene()

scene.add_brain_regions(['CA1'], use_original_color=True, alpha=.2)

# you can pass either the filepaths or the data
scene.add_streamlines(data, color="darkseagreen", show_injection_site=False)

scene.render(camera='sagittal', zoom=1)