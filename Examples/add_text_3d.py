"""
    This example shows how to add 3D text to your scenes
"""

import brainrender
brainrender.SHADER_STYLE = 'cartoon'

from brainrender.scene import Scene
from brainrender.colors import makePalette
from vtkplotter import Text


# Crate a scene
scene = Scene(add_root=False, display_inset=False, use_default_key_bindings=False)


# Text to add
s = 'BRAINRENDER'

# Specify a color for each letter
colors = makePalette('salmon', 'powderblue', N=len(s)+1)

x = 0 # use to specify the position of each letter

# Add letters one at the time to color them individually
for n, letter in enumerate('BRAINRENDER'):
    if 'I' == letter or 'N' == letter and n <5: # make the spacing right 
        x += .6
    else:
        x += dx
    
    # Add letter and silhouette to the scne
    act = Text(letter, depth=.5, c=colors[n], pos=(x, 0, 0), justify='centered')
    sil = act.silhouette().lw(3).color('k')
    scene.add_vtkactor(act, sil)


scene.render()