from vedo import Plane
from vedo.colors import colorMap as map_color
from typing import Optional, Tuple
import numpy as np

from brainrender import Scene
from brainrender.atlas import Atlas
from brainrender import settings, cameras


def check_values(values: dict, atlas: Atlas) -> Tuple[float, float]:
    """
    Checks that the passed heatmap values meet two criteria:
        - keys should be acronyms of brainregions
        - values should be numbers
    """
    for k, v in values.items():
        if not isinstance(v, (float, int)):
            raise ValueError(
                f'Heatmap values should be floats, not: {type(v)} for entry "{k}"'
            )

        if k not in atlas.lookup_df.acronym.values:
            raise ValueError(f'Region name "{k}" not recognized')

    vmax, vmin = max(values.values()), min(values.values())
    return vmax, vmin


def get_planes(
    scene: Scene,
    position: float = 0,
    orientation: str = "frontal",
    thickness: float = 100,
) -> Tuple[Plane, Plane]:
    """
    Returns the two planes used to slices the brainreder scene.
    The planes have different norms based on the desired orientation and
    they're thickness micrometers apart.
    """
    # get the index of the axis
    if orientation == "frontal":
        axidx = 0
    elif orientation == "sagittal":
        axidx = 2
    elif orientation == "top":
        axidx = 1
    else:
        raise ValueError(f'Orientation "{orientation}" not recognized')

    # get the two points the plances are cenered at
    shift = np.zeros(3)
    shift[axidx] -= thickness

    p0 = scene.root._mesh.centerOfMass()
    p1 = scene.root._mesh.centerOfMass()
    p1 -= shift

    # get the two planes
    norm0, norm1 = np.zeros(3), np.zeros(3)
    norm0[axidx] = 1
    norm1[axidx] = -1

    plane0 = scene.atlas.get_plane(pos=p0, norm=tuple(norm0))
    plane1 = scene.atlas.get_plane(pos=p1, norm=tuple(norm1))

    return plane0, plane1


def heatmap_given_planes(
    scene: Scene,
    plane0: Plane,
    plane1: Plane,
    values: dict,
    title: Optional[str] = None,
    cmap: str = "bwr",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
) -> Scene:
    """
    Given a brainrender Scene and two Planes, and a dictionary mapping
    region name -> value, this function adds the brain regions to the scene,
    colored according to the value and then uses the planes to slice all actors.
    """
    # inspect values
    _vmax, _vmin = check_values(values, scene.atlas)
    vmin = vmin or _vmin
    vmax = vmax or _vmax

    # add brain regions to scene
    for region, value in values.items():
        color = list(map_color(value, name=cmap, vmin=vmin, vmax=vmax))
        scene.add_brain_region(region, color=color)

    # slice the scene
    regions = [
        r
        for r in scene.get_actors(br_class="brain region")
        if r.name != "root"
    ]
    for n, plane in enumerate((plane0, plane1)):
        scene.slice(plane, actors=regions, close_actors=True)
    scene.slice(plane0, actors=scene.root, close_actors=False)
    return scene


def heatmap(
    values: dict,
    position: float = 0,
    orientation: str = "frontal",
    thickness: float = 100,
    title: Optional[str] = None,
    cmap: str = "bwr",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    interactive: bool = True,
    zoom: Optional[float] = None,
    atlas_name: Optional[str] = None,
    **kwargs,
) -> Scene:
    """
    Create a heatmap showing scalar values mapped onto brian regions colors
    for a slice through a brain atlas.

    Arguments:
        values: dictionary mapping brain region names to scalar values.
        position: float, position setting where the brain should be sliced (in micrometers).
        orientation: str ('fronta', 'sagitta', 'top'). orientation of the plane slicing through the brain
        thickness: float, thickness of the brian slice.
    """

    # Set settings for heatmap visualization
    settings.SHOW_AXES = False
    settings.SHADER_STYLE = "cartoon"
    settings.BACKGROUND_COLOR = "#050505"
    settings.ROOT_ALPHA = 0.7
    settings.ROOT_COLOR = "w"

    # create a scene
    scene = Scene(
        atlas_name=atlas_name, title=title, title_color="w", **kwargs
    )

    # get the plane position
    plane0, plane1 = get_planes(
        scene, orientation=orientation, position=position, thickness=thickness
    )

    scene = heatmap_given_planes(
        scene,
        plane0,
        plane1,
        values,
        title=title,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
    )

    # render and return
    if orientation == "sagittal":
        camera = cameras.sagittal_camera2
    else:
        camera = orientation
    scene.render(camera=camera, interactive=interactive, zoom=zoom)
    return scene
