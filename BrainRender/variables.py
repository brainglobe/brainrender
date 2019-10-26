""" ------------------------------------------------------------------------------------------------------------------------------------------- """
        # WHOLE SCENE RENDERING OPTIONS
""" ------------------------------------------------------------------------------------------------------------------------------------------- """
DISPLAY_INSET = True            # display a small version of the brain to show the orientation, 
                                # useful when the overall brian is not displayed (DISPLAY_ROOT). inset is crated at render time
DISPLAY_ROOT = True             # display the overall shape of the brain
WHOLE_SCREEN = False            # If true render window is full screen


""" ------------------------------------------------------------------------------------------------------------------------------------------- """
        # BRAIN REGIONS RENDERING OPTIONS
""" ------------------------------------------------------------------------------------------------------------------------------------------- """
DEFAULT_VIP_REGIONS = []        # list of acronyms of regions that must have different colors by default
DEFAULT_VIP_COLOR = [.8, .2, .2]  # default color of VIP regions

ROOT_COLOR = [.8, .8, .8]       # color of the overall brain model's actor
ROOT_ALPHA = .1                 # transparency of the overall brain model's actor'

DEFAULT_STRUCTURE_COLOR = [.8, .8, .8]  
DEFAULT_STRUCTURE_ALPHA = 0.5

""" ------------------------------------------------------------------------------------------------------------------------------------------- """
        # TRACTOGRAPHY & INJECTION RENDERING OPTIONS
""" ------------------------------------------------------------------------------------------------------------------------------------------- """
INJECTION_VOLUME_SIZE = 150    # injection locations are represented as spheres whose radius is injection-volume*INJECTION_VOLUME_SIZE
TRACTO_RADIUS = 20             # radius of tubes used to represent tracts
TRACTO_ALPHA = 1               # transparency of tracts
TRACTO_RES = 12                # resolution of tubes used to represent tracts
TRACT_DEFAULT_COLOR = "r"      # default color of tractography tubes
INJECTION_DEFAULT_COLOR = "g"  # default color for experiments injection sites

""" ------------------------------------------------------------------------------------------------------------------------------------------- """
        # MOUSE LIGHT NEURONS RENDERING VARIABLES
""" ------------------------------------------------------------------------------------------------------------------------------------------- """
DEFAULT_NEURITE_RADIUS = 12     # radius of dendrites, axons...
SOMA_RADIUS = 5 # 50                # radius of the soma sphere
NEURON_RESOLUTION = 16          # resolution of actors used to render the neuron, 
NEURON_ALPHA = 0.85                # transparency of the neurons actors

ML_PARALLEL_PROCESSING = False   # render neurons in parallel to speed things up !! the option is here but this is not supported yet
ML_N_PROCESSES = 6              # max number of processes to use


""" ------------------------------------------------------------------------------------------------------------------------------------------- """
        # OTHER RENDERING VARIABLES
""" ------------------------------------------------------------------------------------------------------------------------------------------- """
SHADER_STYLE = "plastic"         # affects the look of rendered brain regions, valeus can be: [metallic, plastic, shiny, glossy] and can be changed in interactive mode
DECIMATE_NEURONS = False
SMOOTH_NEURONS = True

drosophila_root = "Meshes/drosophila_meshes/JFRC2RindMeshSmooth.obj"

from vtkplotter import settings
settings.useDepthPeeling = True # necessary for rendering of semitransparent actors
settings.useFXAA = True # necessary for rendering of semitransparent actors
settings.screeshotScale = 1  # Improves resolution of saved screenshots

""" ------------------------------------------------------------------------------------------------------------------------------------------- """
        # DEBUG VARIABLES
""" ------------------------------------------------------------------------------------------------------------------------------------------- """
NEURONS_FILE = "Examples/example_files/one_neuron.json"
VERBOSE = True                  # if True print useful messages during use

""" ------------------------------------------------------------------------------------------------------------------------------------------- """
        # SUPPORTED_FILE FORMATS
""" ------------------------------------------------------------------------------------------------------------------------------------------- """
HDF_SUFFIXES = [".h5", ".hdf", ".hdf5", ".he5"]
DEFAULT_HDF_KEY = "df"



""" ------------------------------------------------------------------------------------------------------------------------------------------- """
        # CONSTANTS, SHOULD NOT BE CHANGED
""" ------------------------------------------------------------------------------------------------------------------------------------------- """
INTERACTIVE_MSG = """
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