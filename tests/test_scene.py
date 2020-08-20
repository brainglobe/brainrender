import pytest
import pandas as pd
from vedo import Text, settings

import brainrender
from brainrender.scene import Scene, DualScene, MultiScene
from brainrender.Utils.camera import coronal_camera
from brainrender.colors import makePalette
from brainrender.Utils.scene_utils import get_n_random_points_in_region
from brainrender.Utils.data_manipulation import get_cells_in_region


@pytest.fixture
def scene():
    return Scene()


def test_default():
    brainrender.DISPLAY_INSET
    brainrender.DISPLAY_ROOT
    brainrender.WHOLE_SCREEN
    brainrender.BACKGROUND_COLOR
    brainrender.SHOW_AXES
    brainrender.WINDOW_POS
    brainrender.CAMERA
    brainrender.DEFAULT_SCREENSHOT_NAME
    brainrender.DEFAULT_SCREENSHOT_TYPE
    brainrender.SCREENSHOT_TRANSPARENT_BACKGROUND
    brainrender.ROOT_COLOR
    brainrender.ROOT_ALPHA
    brainrender.DEFAULT_STRUCTURE_COLOR
    brainrender.DEFAULT_STRUCTURE_ALPHA
    brainrender.INJECTION_VOLUME_SIZE
    brainrender.TRACTO_RADIUS
    brainrender.TRACTO_ALPHA
    brainrender.TRACTO_RES
    brainrender.TRACT_DEFAULT_COLOR
    brainrender.INJECTION_DEFAULT_COLOR
    brainrender.STREAMLINES_RESOLUTION
    brainrender.INJECTION_VOLUME_SIZE
    brainrender.TRACTO_RADIUS
    brainrender.TRACTO_ALPHA
    brainrender.TRACTO_RES
    brainrender.TRACT_DEFAULT_COLOR
    brainrender.INJECTION_DEFAULT_COLOR
    brainrender.STREAMLINES_RESOLUTION
    brainrender.SHADER_STYLE
    brainrender.VERBOSE
    brainrender.HDF_SUFFIXES
    brainrender.DEFAULT_HDF_KEY

    brainrender.reset_defaults()


def test_scene_creation():
    Scene()


def test_scene_creation_ignore_inset():
    Scene(display_inset=False)


def test_scene_creation_ignore_root():
    Scene(add_root=False)


def test_scene_creation_ignore_root_and_inset():
    s = Scene(add_root=False, display_inset=False)
    s.render(interactive=False)
    s.close()


def test_scene_creation_default_keys():
    Scene(use_default_key_bindings=True)


def test_scene_creation_camera():
    Scene(camera="sagittal")
    Scene(camera=coronal_camera)


def test_scene_creation_title():
    Scene(title="My title")


def test_scene_creation_notebook():
    settings.notebookBackend = "k3d"
    Scene()
    settings.notebookBackend = None


def test_scene_creation_settings():
    brainrender.SHOW_AXES = True
    brainrender.WHOLE_SCREEN = False
    Scene()
    brainrender.SHOW_AXES = False


@pytest.mark.slow
def test_scene_creation_brainglobe():
    scene = Scene(atlas="allen_mouse_25um")

    try:
        scene.add_brain_regions("TH")
    except:
        raise ValueError

    try:
        scene.add_streamlines
    except:
        raise ValueError

    scene = Scene(atlas="allen_human_500um")
    try:
        scene.add_brain_regions("TH")
    except:
        raise ValueError


def test_root(scene):
    scene.add_root()


def test_regions():
    scene = Scene(camera=coronal_camera)
    regions = ["MOs", "VISp", "ZI"]
    scene.add_brain_regions(regions, colors="green")
    ca1 = scene.add_brain_regions("CA1", add_labels=True)
    ca1.alpha(0.2)
    scene.close()


def test_cut_with_plane(scene):
    # Add some actors
    scene.add_brain_regions(["MOp"], alpha=0.5)

    # Specify position, size and orientation of the plane
    pos = scene.atlas._root_midpoint
    norm = [0, 1, 1]
    plane = scene.atlas.get_plane_at_point(pos, norm, color="lightblue")

    # Cut
    scene.cut_actors_with_plane(
        plane, close_actors=False, showplane=True, actors=scene.root,
    )
    scene.cut_actors_with_plane(
        plane, close_actors=True, showplane=False,
    )

    scene.cut_actors_with_plane(["sagittal", "frontal", "horizontal"])


def test_add_plane(scene):
    scene.add_plane(plane="sagittal")


def test_camera():
    # Create a scene
    scene = Scene(camera="top")  # specify that you want a view from the top

    # render
    scene.render(interactive=False,)
    scene.close()

    # Now render but with a different view
    scene = Scene()
    scene.render(interactive=False, camera="sagittal", zoom=1)
    scene.close()

    # Now render but with specific camera parameters
    bespoke_camera = dict(
        position=[801.843, -1339.564, 8120.729],
        focal=[9207.34, 2416.64, 5689.725],
        viewup=[0.36, -0.917, -0.171],
        distance=9522.144,
        clipping=[5892.778, 14113.736],
    )

    scene = Scene()
    scene.render(interactive=False, camera=bespoke_camera, zoom=1)
    scene.close()


def test_text_3d(scene):
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

        # Add letter and silhouette to the scne
        act = Text(
            letter, depth=0.5, c=colors[n], pos=(x, 0, 0), justify="centered"
        )
        sil = act.silhouette().lw(3).color("k")
        scene.add_actor(act, sil)

    scene.render(interactive=False)
    scene.close()


def text_actor_labels(scene):
    # add_brain_regions can be used to add labels directly
    scene.add_brain_regions("VAL", add_labels=True)

    # you can also use scene.add_actor_label
    mos = scene.add_brain_regions("MOs")

    # Add another label, this time make it gray and shift it slightly
    scene.add_actor_label(
        mos, "MOs", size=400, color="blackboard", xoffset=250
    )


def test_crosshair(scene):
    scene.add_brain_regions(["TH"], use_original_color=False, alpha=0.4)

    # Add a point in the right hemisphere
    point = scene.atlas.get_region_CenterOfMass("TH")
    scene.add_crosshair_at_point(
        point,
        point_kwargs={
            "color": "salmon"
        },  # specify how the point at the center of the crosshair looks like
    )

    # Add a point in the left hemisphere
    point = scene.atlas.get_region_CenterOfMass("TH", hemisphere="left")
    scene.add_crosshair_at_point(
        point,
        point_kwargs={
            "color": "darkseagreen"
        },  # specify how the point at the center of the crosshair looks like
    )


def test_cells_from_file(scene):
    scene.add_cells_from_file("tests/data/cells.csv")
    scene.add_cells_from_file("tests/data/cells.h5")


def test_labelled_cells(scene):
    # Gerate the coordinates of N cells across 3 regions
    _regions = ["MOs", "VISp", "ZI"]
    N = 100  # getting 1k cells per region, but brainrender can deal with >1M cells easily.

    # Render regions
    scene.add_brain_regions(_regions, alpha=0.2)

    # Get fake cell coordinates
    cells, regions = [], []  # to store x,y,z coordinates
    for region in _regions:
        region_cells = get_n_random_points_in_region(
            scene.atlas, region=region, N=N
        )
        if len(region_cells) != N:
            raise ValueError
        cells.extend(region_cells)
        regions.extend([region for i in region_cells])
    x, y, z = (
        [c[0] for c in cells],
        [c[1] for c in cells],
        [c[2] for c in cells],
    )
    cells = pd.DataFrame(dict(x=x, y=y, z=z, region=regions))
    # Add cells
    scene.add_cells(cells, color="darkseagreen", res=12, radius=25)
    get_cells_in_region(scene.atlas, cells, "MOs")
    scene.add_cells(cells, color_by_metadata="x")
    scene.add_cells(
        cells,
        color_by_metadata="x",
        color={x: "salmon" for x in cells.x.values},
    )
    scene.add_cells(cells, color_by_region=True, radius=50, res=25)


def test_get_random_points(scene):
    get_n_random_points_in_region(scene.atlas, "MOs", 100)
    get_n_random_points_in_region(scene.atlas, "MOp", 100, hemisphere="right")
    ca1 = scene.add_brain_regions("CA1")
    get_n_random_points_in_region(scene.atlas, ca1, 100)


def test_add_from_file(scene):
    scene.add_from_file("Examples/example_files/skull.stl")


def test_add_sphere(scene):
    scene.add_sphere_at_point()


def test_add_optic_cannula(scene):
    scene.add_optic_cannula(target_region="CA1")

    p0 = scene.atlas.get_region_CenterOfMass("MOs")
    scene.add_optic_cannula(pos=p0)


def test_sharptrack(scene):
    scene.add_probe_from_sharptrack(
        "Examples/example_files/sharptrack_probe_points.mat"
    )


@pytest.mark.slow
def test_export_for_web(scene):
    scene.export_for_web()


def test_multi_scenes():
    df = DualScene()
    df.render(_interactive=False)
    df.close()

    ms = MultiScene(3)
    ms.render(_interactive=False)
    ms.close()


def test_screenshot(scene):
    scene.take_screenshot()
    scene.render(interactive=False)
    scene.take_screenshot()
    scene.close()


def test_add_actor(scene):
    act = scene.add_brain_regions("MOs")
    scene.add_actor(act)
