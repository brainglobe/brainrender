import os
import sys
import brainrender.default_variables
from brainrender.Utils.data_io import save_yaml

# -------------------------- Set vtkplotter shaders -------------------------- #
from vtkplotter import settings
settings.useDepthPeeling = True # necessary for rendering of semitransparent actors
settings.useFXAA = True # necessary for rendering of semitransparent actors
settings.screeshotScale = 1  # Improves resolution of saved screenshots


# ------------------------- reset default parameters file ------------------------- #
def reset_defaults():
    pathtofile = os.path.join(os.path.expanduser("~"), ".brainrender", 'config.yaml')
    
    # Get all variables from defaults
    vs = {key: value for key, value in default_variables.__dict__.items() 
                    if not (key.startswith('__') or key.startswith('_'))}
    comment = '# Rendering options. An explanation for each parameter can be found ' +\
                'in the documentation or in brainrender.default_variables.py\n'
    save_yaml(pathtofile, vs, append=False, topcomment=comment)


# ---------------------------------------------------------------------------- #
#                Create a config file from the default variables               #
# ---------------------------------------------------------------------------- #
# Get base directory
user_dir = os.path.expanduser("~")
if not os.path.isdir(user_dir):
    raise FileExistsError("Could not find user base folder (to save brainrender data). Platform: {}".format(sys.platform))
base_dir = os.path.join(user_dir, ".brainrender")

if not os.path.isdir(base_dir):
    os.makedir(base_dir)

# Create config path
config_path = os.path.join(base_dir, 'config.yaml')
if not os.path.isfile(config_path):
    reset_defaults()


