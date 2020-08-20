""" --------------------------------------------------------------------------------- """
# ATLAS
""" --------------------------------------------------------------------------------- """
DEFAULT_ATLAS = "allen_mouse_25um"  # default atlas

""" --------------------------------------------------------------------------------- """
# WHOLE SCENE RENDERING OPTIONS
""" --------------------------------------------------------------------------------- """
DISPLAY_INSET = (
    True  # display a small version of the brain to show the orientation,
)
# useful when the overall brian is not displayed (DISPLAY_ROOT). inset is crated at render time
DISPLAY_ROOT = True  # display the overall shape of the brain
WHOLE_SCREEN = True  # If true render window is full screen
BACKGROUND_COLOR = (
    "white"  # Secify the color of the background window (see colors.py)
)
SHOW_AXES = (
    False  # If true a triad of orthogonal axes is used to show orientation
)
WINDOW_POS = (
    10,
    10,
)  # Position of the window in pixels from bottom left of screen. Only applies when not in fullscreen
CAMERA = "three_quarters"  # Default camera settings (orientation etc. see brainrender.camera.py)

""" --------------------------------------------------------------------------------- """
# SCREENSHOTS AND EXPORT OPTIONS
""" --------------------------------------------------------------------------------- """
DEFAULT_SCREENSHOT_NAME = "screenshot"  # screenshots will have this name and the time at which they were taken
SCREENSHOT_TRANSPARENT_BACKGROUND = (
    True  # If true the screenshots are saved with a transparent background
)

""" --------------------------------------------------------------------------------- """
# BRAIN REGIONS RENDERING OPTIONS
""" --------------------------------------------------------------------------------- """
ROOT_COLOR = [0.8, 0.8, 0.8]  # color of the overall brain model's actor
ROOT_ALPHA = 0.2  # transparency of the overall brain model's actor'
DEFAULT_STRUCTURE_COLOR = [0.8, 0.8, 0.8]
DEFAULT_STRUCTURE_ALPHA = 1


""" --------------------------------------------------------------------------------- """
# TRACTOGRAPHY & INJECTION RENDERING OPTIONS
""" --------------------------------------------------------------------------------- """
INJECTION_VOLUME_SIZE = 120  # injection locations are represented as spheres whose radius is injection-volume*INJECTION_VOLUME_SIZE
TRACTO_RADIUS = 20  # radius of tubes used to represent tracts
TRACTO_ALPHA = 1  # transparency of tracts
TRACTO_RES = 12  # resolution of tubes used to represent tracts
TRACT_DEFAULT_COLOR = "r"  # default color of tractography tubes
INJECTION_DEFAULT_COLOR = "g"  # default color for experiments injection sites
STREAMLINES_RESOLUTION = 3  # resolution of actors used to render the neuron,


""" --------------------------------------------------------------------------------- """
# MOUSE LIGHT NEURONS RENDERING VARIABLES
""" --------------------------------------------------------------------------------- """
DEFAULT_NEURITE_RADIUS = (
    8  # rneurites (axon/dendrites) radius as a fraction of soma radius
)
SOMA_RADIUS = 4  # radius of the soma sphere
NEURON_RESOLUTION = 16  # resolution of actors used to render the neuron,
NEURON_ALPHA = 0.85  # transparency of the neurons actors

""" --------------------------------------------------------------------------------- """
# OTHER VARIABLES
""" --------------------------------------------------------------------------------- """
SHADER_STYLE = "plastic"  # affects the look of rendered brain regions: [metallic, plastic, shiny, glossy]
VERBOSE = True  # if True print useful messages during use

""" --------------------------------------------------------------------------------- """
# SUPPORTED_FILE FORMATS
""" --------------------------------------------------------------------------------- """
HDF_SUFFIXES = [".h5", ".hdf", ".hdf5", ".he5"]
DEFAULT_HDF_KEY = "hdf"
