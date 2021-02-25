from brainrender import settings
from vedo import Box

# set brainrender settings
settings.SHOW_AXES = False
settings.LW = 2
settings.WHOLE_SCREEN = True
settings.SHADER_STYLE = "cartoon"
settings.ROOT_ALPHA = 0.3 if settings.SHADER_STYLE == "cartoon" else 0.2

# useful variables used across figures
LW = 2
INSET = False
SILHOUETTE = True


def root_box(scene):
    """
    Creates a transparent box around the root mesh
    of a brainrender region. This forces the camera to stay in place
    even if ther root mesh is changed (e.g. sliced)
    """
    pos = scene.root.centerOfMass()
    bounds = scene.root.bounds()
    bds = [
        bounds[1] - bounds[0],
        bounds[3] - bounds[2],
        bounds[5] - bounds[4],
    ]

    scene.add(
        Box(
            pos=[pos[0] - 1300, pos[1] - 500, pos[2]],
            length=bds[0],
            width=bds[1],
            height=bds[2],
        ).alpha(0),
        names="box",
        br_classes="box",
    )
