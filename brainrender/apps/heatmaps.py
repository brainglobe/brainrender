from vedo import Plane
from vedo.colors import colorMap as map_color
from typing import Optional, Tuple, Union
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
    orientation: Union[str, tuple] = "frontal",
    thickness: float = 100,
) -> Tuple[Plane, Plane]:
    """
    Returns the two planes used to slices the brainreder scene.
    The planes have different norms based on the desired orientation and
    they're thickness micrometers apart.
    """
    if isinstance(orientation, str):
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
    else:
        orientation = np.array(orientation)

        p0 = scene.root._mesh.centerOfMass()
        p1 = p0 + orientation * thickness

        norm0 = orientation
        norm1 = -orientation

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
) -> Tuple[Scene, dict]:
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
    regions = [
        r
        for r in scene.get_actors(br_class="brain region")
        if r.name != "root"
    ]

    # get plane/regions intersections in plane's coordinates system
    projected = get_plane_regions_intersections(plane0, regions)

    # slice the scene
    for n, plane in enumerate((plane0, plane1)):
        scene.slice(plane, actors=regions, close_actors=True)

    scene.slice(plane0, actors=scene.root, close_actors=False)
    return scene, projected


def get_plane_regions_intersections(
    plane: Plane, regions_actors: list, **kwargs
) -> dict:
    """
    It computes the intersection between the first slice plane and all brain regions,
    returning the coordinates of each region as a set of XY (i.e. in the plane's
    coordinates system) coordinates
    """
    pts = plane.points() - plane.points()[0]
    v = pts[1] / np.linalg.norm(pts[1])
    w = pts[2] / np.linalg.norm(pts[2])

    M = np.vstack([v, w]).T  # 3 x 2

    projected = {}
    for n, actor in enumerate(regions_actors):
        # get region/plane intersection points
        intersection = plane.intersectWith(
            actor._mesh
        ).points()  # points: (N x 3)
        projected[actor.name] = intersection @ M

    return projected


def heatmap(
    values: Union[list, dict],
    position: float = 0,
    orientation: Union[str, tuple] = "frontal",
    thickness: float = 10,
    title: Optional[str] = None,
    cmap: str = "bwr",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    interactive: bool = True,
    zoom: Optional[float] = None,
    atlas_name: Optional[str] = None,
    **kwargs,
) -> Tuple[Scene, dict]:
    """
    Create a heatmap showing scalar values mapped onto brian regions colors
    for a slice through a brain atlas.

    Arguments:
        values: dictionary mapping brain region names to scalar values or list of brain regions names.
        position: float, position setting where the brain should be sliced (in micrometers).
        orientation: str ('fronta', 'sagitta', 'top') or tuple specifying a vector in R^3. orientation of the plane slicing through the brain
        thickness: float, thickness of the brian slice.
    """
    if isinstance(values, list):
        values = {r: 1 for r in values}

    # Set settings for heatmap visualization
    settings.SHOW_AXES = False
    settings.SHADER_STYLE = "cartoon"
    settings.BACKGROUND_COLOR = "#242424"
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

    # create heatmap
    scene, projected = heatmap_given_planes(
        scene,
        plane0,
        plane1,
        values,
        title=title,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
    )

    # # render and return
    if isinstance(orientation, str):
        if orientation == "sagittal":
            camera = cameras.sagittal_camera2
        else:
            camera = orientation
    else:
        orientation = np.array(orientation)
        com = plane0.centerOfMass()
        camera = {
            "pos": com - orientation * 2 * np.linalg.norm(com),
            "viewup": (0, -1, 0),
            "clippingRange": (19531, 40903),
            # 'focalPoint':com,
            # 'distance':np.linalg.norm(com)
        }
        # camera = None
    scene.render(camera=camera, interactive=interactive, zoom=zoom)
    return scene, projected


if __name__ == "__main__":
    # import matplotlib.pyplot as plt

    values = dict(  # scalar values for each region
        TH=1,
        RSP=0.2,
        AI=0.4,
        SS=-3,
        MO=2.6,
        PVZ=-4,
        LZ=-3,
        VIS=2,
        AUD=0.3,
        RHP=-0.2,
        STR=0.5,
        CB=0.5,
        FRP=-1.7,
        HIP=3,
        PA=-4,
    )

    scene, projected = heatmap(
        values,
        position=5200,  # displacement along the AP axis relative to midpoint
        orientation="frontal",  # or 'sagittal', or 'top' or a tuple (x,y,z)
        thickness=10,  # thickness of the slices used for rendering (in microns)
        title="frontal",
        vmin=-5,
        vmax=3,
    )
    scene.close()  # avoid showing it

    # print("showing plot")
    # f, ax = plt.subplots(figsize=(9, 9))
    # for r, coords in projected.items():
    #     ax.fill(coords[:, 0], coords[:, 1], label=r)

    # ax.legend()
    # plt.show()
