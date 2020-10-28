"""
    This example shows how to add 3D text to your scenes
"""

import brainrender

brainrender.SHADER_STYLE = "cartoon"

from brainrender.scene import Scene
from brainrender.colors import makePalette
from vedo import Text


camera = dict(
    {
        "position": (4.58173814842751, 1.3170832519052862, 28.807539941401348),
        "focal": (5.63320729136467, 0.0, 0.13752250373363495),
        "viewup": (
            0.008857944291024357,
            0.9989221022772287,
            -0.04556501294830602,
        ),
        "distance": 28.719508970857582,
        "clipping": (27.608253763329618, 30.187623512524752),
        "orientation": (
            2.62851947276041,
            2.1003738639279446,
            0.41150325521778314,
        ),
    }
)

# Crate a scene
scene = Scene(
    add_root=False,
    display_inset=False,
    use_default_key_bindings=False,
    camera=camera,
)


# Text to add
s = "BRAINRENDER"

# Specify a color for each letter
colors = makePalette(len(s), "salmon", "powderblue")

x = 0  # use to specify the position of each letter

# Add letters one at the time to color them individually
for n, letter in enumerate("BRAINRENDER"):
    if "I" == letter or "N" == letter and n < 5:  # make the spacing right
        x += 0.6
    else:
        x += 1

    # Add letter and silhouette to the scene
    act = Text(
        letter,
        depth=0.5,
        c=colors[n],
        pos=(x, 0, 0),
        justify="centered",
        alpha=1,
    )

    scene.add_silhouette(act, lw=3)


scene.render()
