"""
Brainrender provides several default settins (e.g. for shader style)
which can be changed to personalize your rendering. 
This example shows you how
"""

import brainrender
from brainrender import Scene

from rich import print
from myterial import orange
from pathlib import Path

print(f"[{orange}]Running example: {Path(__file__).name}")

brainrender.settings.BACKGROUND_COLOR = [
    0.22,
    0.22,
    0.22,
]  # change rendering background color
brainrender.settings.WHOLE_SCREEN = (
    False  # make the rendering window be smaller
)

# make scenes with different shader styles
for shader in ("plastic", "cartoon"):
    brainrender.settings.SHADER_STYLE = shader
    scene = Scene(title=shader)
    scene.render()
