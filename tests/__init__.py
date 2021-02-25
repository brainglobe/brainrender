from brainrender import settings

settings.INTERACTIVE = False
settings.OFFSCREEN = True

from vedo import settings as vsettings

vsettings.useDepthPeeling = False
vsettings.screenshotTransparentBackground = False  # vedo for transparent bg
vsettings.useFXAA = True  # This needs to be false for transparent bg
