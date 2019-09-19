""" ------------------------------------------------------------------------------------------------------------------------------------------- """
        # WHOLE SCENE RENDERING OPTIONS
""" ------------------------------------------------------------------------------------------------------------------------------------------- """
VERBOSE = False                  # if True print useful messages during use
DISPLAY_INSET = True            # display a small version of the brain to show the orientation, 
                                # useful when the overall brian is not displayed (DISPLAY_ROOT). inset is crated at render time
DISPLAY_ROOT = True             # display the overall shape of the brain

DEFAULT_VIP_REGIONS = []        # list of acronyms of regions that must have different colors by default
DEFAULT_VIP_COLOR = [.8, .2, .2]  # default color of VIP regions

ROOT_COLOR = [.8, .8, .8]       # color of the overall brain model's actor
ROOT_ALPHA = .3                 # transparency of the overall brain model's actor'

DEFAULT_STRUCTURE_COLOR = [.8, .8, .8]  
DEFAULT_STRUCTURE_ALPHA = 1


""" ------------------------------------------------------------------------------------------------------------------------------------------- """
        # MOUSE LIGHT NEURONS RENDERING VARIABLES
""" ------------------------------------------------------------------------------------------------------------------------------------------- """
DEFAULT_NEURITE_RADIUS = 10     # radius of dendrites, axons...
SOMA_RADIUS = 50                # radius of the soma sphere
NEURON_RESOLUTION = 24          # resolution of actors used to render the neuron, values of 12,24 are fine
NEURON_ALPHA = 1                # transparency of the neurons actors




""" ------------------------------------------------------------------------------------------------------------------------------------------- """
        # DEBUG VARIABLES
""" ------------------------------------------------------------------------------------------------------------------------------------------- """
NEURONS_FILE = "D:\\Dropbox (UCL - SWC)\\Rotation_vte\\analysis_metadata\\anatomy\\Mouse Light\\neurons_in_PAG.json"