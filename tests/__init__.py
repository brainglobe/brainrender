from brainrender import settings

settings.INTERACTIVE = False
settings.OFFSCREEN = True
settings.DEFAULT_ATLAS = "allen_mouse_100um"

from vedo import settings as vsettings

vsettings.use_depth_peeling = False
vsettings.screenshot_transparent_background = False  # vedo for transparent bg
vsettings.use_fxaa = True  # This needs to be false for transparent bg
