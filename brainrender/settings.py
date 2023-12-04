import sys

from vedo import settings as vsettings

DEBUG = False  # set to True to see more detailed logs

# ------------------------------- vedo settings ------------------------------ #

vsettings.point_smoothing = False
vsettings.line_smoothing = False
vsettings.polygon_smoothing = False
vsettings.immediate_rendering = False

vsettings.use_depth_peeling = True
vsettings.alpha_bit_planes = 1
vsettings.max_number_of_peels = 12
vsettings.occlusion_ratio = 0.1
vsettings.multi_samples = 0 if sys.platform == "darwin" else 8

# For transparent background with screenshots
vsettings.screenshot_transparent_background = False  # vedo for transparent bg
vsettings.use_fxaa = False


# --------------------------- brainrender settings --------------------------- #

BACKGROUND_COLOR = "white"
DEFAULT_ATLAS = "allen_mouse_25um"  # default atlas
DEFAULT_CAMERA = "three_quarters"  # Default camera settings (orientation etc. see brainrender.camera.py)
INTERACTIVE = True  # rendering interactive ?
LW = 2  # e.g. for silhouettes
ROOT_COLOR = [0.8, 0.8, 0.8]  # color of the overall brain model's actor
ROOT_ALPHA = 0.2  # transparency of the overall brain model's actor'
SCREENSHOT_SCALE = 1
SHADER_STYLE = "cartoon"  # affects the look of rendered brain regions: [metallic, plastic, shiny, glossy]
SHOW_AXES = True
WHOLE_SCREEN = False  # If true render window is full screen
OFFSCREEN = False
