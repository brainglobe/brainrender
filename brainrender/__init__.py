import os
import sys
import brainrender.default_variables
from brainrender.Utils.data_io import save_yaml, load_yaml


__all__ = [
    "BACKGROUND_COLOR",
    "DECIMATE_NEURONS",
    "DEFAULT_HDF_KEY",
    "DEFAULT_NEURITE_RADIUS",
    "DEFAULT_STRUCTURE_ALPHA",
    "DEFAULT_STRUCTURE_COLOR",
    "DEFAULT_VIP_COLOR",
    "DEFAULT_VIP_REGIONS",
    "DISPLAY_INSET",
    "DISPLAY_ROOT",
    "HDF_SUFFIXES",
    "INJECTION_DEFAULT_COLOR",
    "INJECTION_VOLUME_SIZE",
    "NEURON_ALPHA",
    "NEURON_RESOLUTION",
    "ROOT_ALPHA",
    "ROOT_COLOR",
    "SHADER_STYLE",
    "SHOW_AXES",
    "SMOOTH_NEURONS",
    "SOMA_RADIUS",
    "STREAMLINES_RESOLUTION",
    "TRACTO_ALPHA",
    "TRACTO_RADIUS",
    "TRACTO_RES",
    "TRACT_DEFAULT_COLOR",
    "USE_MORPHOLOGY_CACHE",
    "VERBOSE",
    "WHOLE_SCREEN",
    "WINDOW_POS",
    "INTERACTIVE_MSG",
    "CAMERA",
    "DEFAULT_SCREENSHOT_NAME",
    "DEFAULT_SCREENSHOT_TYPE",
    "DEFAULT_SCREENSHOT_SCALE",
    ]


# -------------------------- Set vtkplotter shaders -------------------------- #
from vtkplotter import settings
settings.useDepthPeeling = True # necessary for rendering of semitransparent actors
settings.useFXAA = True # necessary for rendering of semitransparent actors
settings.screeshotScale = 1  # Improves resolution of saved screenshots


# ------------------------- reset default parameters file ------------------------- #
params_file = os.path.join(os.path.expanduser("~"), ".brainrender", 'config.yaml')
defaults = brainrender.default_variables.__dict__
comment = '# Rendering options. An explanation for each parameter can be found ' +\
            'in the documentation or in brainrender.default_variables.py\n'

def reset_defaults():
    # Get all variables from defaults
    vs = {key: value for key, value in defaults.items() 
                    if not (key.startswith('__') or key.startswith('_'))}
    save_yaml(params_file, vs, append=False, topcomment=comment)


# ---------------------------------------------------------------------------- #
#                Create a config file from the default variables               #
# ---------------------------------------------------------------------------- #
# Get base directory
_user_dir = os.path.expanduser("~")
if not os.path.isdir(_user_dir):
    raise FileExistsError("Could not find user base folder (to save brainrender data). Platform: {}".format(sys.platform))
_base_dir = os.path.join(_user_dir, ".brainrender")

if not os.path.isdir(_base_dir):
    os.mkdir(_base_dir)

# Create config path
_config_path = os.path.join(_base_dir, 'config.yaml')
if not os.path.isfile(_config_path):
    reset_defaults()


# ---------------------------------------------------------------------------- #
#                                PARSE VARIABLES                               #
# ---------------------------------------------------------------------------- #
# Rendering options. An explanation for each parameter can be found in the documentation or in brainrender.default_variables.py
params = load_yaml(_config_path)

# Check we have all the params
for par in __all__:
    if par in ['INTERACTIVE_MSG']:
        continue
    if par not in params.keys():
        params[par] = defaults[par]
save_yaml(params_file, params, append=False, topcomment=comment)


# Set to make it easy to import
BACKGROUND_COLOR = params['BACKGROUND_COLOR']
DECIMATE_NEURONS = params['DECIMATE_NEURONS']
DEFAULT_HDF_KEY = params['DEFAULT_HDF_KEY']
DEFAULT_NEURITE_RADIUS = params['DEFAULT_NEURITE_RADIUS']
DEFAULT_STRUCTURE_ALPHA = params['DEFAULT_STRUCTURE_ALPHA']
DEFAULT_STRUCTURE_COLOR = params['DEFAULT_STRUCTURE_COLOR']
DEFAULT_VIP_COLOR = params['DEFAULT_VIP_COLOR']
DEFAULT_VIP_REGIONS = params['DEFAULT_VIP_REGIONS']
DISPLAY_INSET = params['DISPLAY_INSET']
DISPLAY_ROOT = params['DISPLAY_ROOT']
HDF_SUFFIXES = params['HDF_SUFFIXES']
INJECTION_DEFAULT_COLOR = params['INJECTION_DEFAULT_COLOR']
INJECTION_VOLUME_SIZE = params['INJECTION_VOLUME_SIZE']
NEURON_ALPHA = params['NEURON_ALPHA']
NEURON_RESOLUTION = params['NEURON_RESOLUTION']
ROOT_ALPHA = params['ROOT_ALPHA']
ROOT_COLOR = params['ROOT_COLOR']
SHADER_STYLE = params['SHADER_STYLE']
SHOW_AXES = params['SHOW_AXES']
SMOOTH_NEURONS = params['SMOOTH_NEURONS']
SOMA_RADIUS = params['SOMA_RADIUS']
STREAMLINES_RESOLUTION = params['STREAMLINES_RESOLUTION']
TRACTO_ALPHA = params['TRACTO_ALPHA']
TRACTO_RADIUS = params['TRACTO_RADIUS']
TRACTO_RES = params['TRACTO_RES']
TRACT_DEFAULT_COLOR = params['TRACT_DEFAULT_COLOR']
USE_MORPHOLOGY_CACHE = params['USE_MORPHOLOGY_CACHE']
VERBOSE = params['VERBOSE']
WHOLE_SCREEN = params['WHOLE_SCREEN']
WINDOW_POS = params['WINDOW_POS']
CAMERA = params['CAMERA']
DEFAULT_SCREENSHOT_NAME = params['DEFAULT_SCREENSHOT_NAME']
DEFAULT_SCREENSHOT_TYPE = params['DEFAULT_SCREENSHOT_TYPE']
DEFAULT_SCREENSHOT_SCALE = params['DEFAULT_SCREENSHOT_SCALE']

INTERACTIVE_MSG = \
"""
 ==========================================================
| Press: i     print info about selected object            |
|        m     minimise opacity of selected mesh           |
|        .,    reduce/increase opacity                     |
|        /     maximize opacity                            |
|        w/s   toggle wireframe/solid style                |
|        p/P   change point size of vertices               |
|        l     toggle edges line visibility                |
|        x     toggle mesh visibility                      |
|        X     invoke a cutter widget tool                 |
|        1-3   change mesh color                           |
|        4     use scalars as colors, if present           |
|        5     change background color                     |
|        0-9   (on keypad) change axes style               |
|        k     cycle available lighting styles             |
|        K     cycle available shading styles              |
|        o/O   add/remove light to scene and rotate it     |
|        n     show surface mesh normals                   |
|        a     toggle interaction to Actor Mode            |
|        j     toggle interaction to Joystick Mode         |
|        r     reset camera position                       |
|        C     print current camera info                   |
|        S     save a screenshot                           |
|        E     export rendering window to numpy file       |
|        q     return control to python script             |
|        Esc   close the rendering window and continue     |
|        F1    abort execution and exit python kernel      |
| Mouse: Left-click    rotate scene / pick actors          |
|        Middle-click  pan scene                           |
|        Right-click   zoom scene in or out                |
|        Cntrl-click   rotate scene perpendicularly        |
|----------------------------------------------------------|
| Check out documentation at:  https://vtkplotter.embl.es  |
 ==========================================================
"""




