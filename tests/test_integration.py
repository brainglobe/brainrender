from pathlib import Path

import imio
import numpy as np
import pooch
import pytest
from bg_space import AnatomicalSpace
from vedo import Volume as VedoVolume

from brainrender import Animation, Scene, VideoMaker
from brainrender.actors import (
    Neuron,
    Points,
    PointsDensity,
    Volume,
    ruler,
    ruler_from_surface,
)
from brainrender.atlas_specific import GeneExpressionAPI


def get_n_points_in_region(region, N):
    """
    Gets N points inside (or on the surface) of a mes
    """

    region_bounds = region.mesh.bounds()
    X = np.linspace(region_bounds[0], region_bounds[1], num=N)
    Y = np.linspace(region_bounds[2], region_bounds[3], num=N)
    Z = np.linspace(region_bounds[4], region_bounds[5], num=N)
    pts = [[x, y, z] for x, y, z in zip(X, Y, Z)]

    ipts = region.mesh.inside_points(pts).points()
    return np.vstack(ipts)


def check_bounds(bounds, parent_bounds):
    """
    Checks that the bounds of an actor are within the bounds of the root
    """
    for i, bound in enumerate(bounds):
        if i % 2 == 0:
            assert bound >= parent_bounds[i]
        else:
            assert bound <= parent_bounds[i]


@pytest.fixture
def scene():
    scene = Scene(atlas_name="allen_mouse_100um", inset=False)
    yield scene
    scene.close()
    del scene


def test_scene_with_brain_region(scene):
    brain_region = scene.add_brain_region(
        "grey",
        alpha=0.4,
    )

    bounds = brain_region.bounds()
    root_bounds = scene.root.bounds()

    assert scene.actors[1] == brain_region

    check_bounds(bounds, root_bounds)


def test_add_cells(scene):
    mos = scene.add_brain_region("MOs", alpha=0.15)
    coordinates = get_n_points_in_region(mos, 1000)
    points = Points(coordinates, name="CELLS", colors="steelblue")

    scene.add(points)

    assert scene.actors[0] == scene.root
    assert scene.actors[1] == mos
    assert scene.actors[2] == points

    scene.render(interactive=False)

    root_bounds = scene.root.bounds()
    region_bounds = mos.bounds()
    points_bounds = points.bounds()

    check_bounds(points_bounds, root_bounds)
    check_bounds(region_bounds, root_bounds)


def test_add_labels(scene):
    th, mos = scene.add_brain_region("TH", "MOs")
    scene.add_label(th, "TH")

    scene.render(interactive=False)

    assert scene.actors[1] == th
    assert scene.actors[2] == mos
    assert len(th.labels) == 2
    assert len(mos.labels) == 0

    th_label_text_bounds = th.labels[0].bounds()
    th_label_bounds = th.labels[1].bounds()
    root_bounds = scene.root.bounds()

    check_bounds(th_label_text_bounds, root_bounds)
    check_bounds(th_label_bounds, root_bounds)


def test_add_mesh_from_file(scene, pytestconfig):
    root_path = pytestconfig.rootpath
    scene.add_brain_region("SCm", alpha=0.2)
    file_mesh = scene.add(
        root_path / "tests" / "files" / "CC_134_1_ch1inj.obj", color="tomato"
    )

    scene.render(interactive=False)

    file_mesh_bounds = file_mesh.bounds()
    root_bounds = scene.root.bounds()

    check_bounds(file_mesh_bounds, root_bounds)


def test_animation(scene, pytestconfig):
    root_path = pytestconfig.rootpath
    vid_directory = root_path / "tests" / "examples"

    scene.add_brain_region("TH")
    anim = Animation(scene, vid_directory, "vid3")

    anim.add_keyframe(0, camera="top", zoom=1)
    anim.add_keyframe(1.5, camera="sagittal", zoom=0.95)
    anim.add_keyframe(3, camera="frontal", zoom=1)
    anim.add_keyframe(4, camera="frontal", zoom=1.2)

    anim.make_video(duration=5, fps=15)

    scene.render(interactive=False)
    scene.close()

    vid_path = Path(root_path / "tests" / "examples" / "vid3.mp4")

    assert vid_path.exists()
    vid_path.unlink()
    Path.rmdir(vid_directory)


def test_adding_multiple_brain_regions(scene):
    th = scene.add_brain_region("TH")
    brain_regions = scene.add_brain_region(
        "MOs", "CA1", alpha=0.2, color="green"
    )

    scene.render(interactive=False)

    assert len(scene.actors) == 4
    assert scene.actors[1].name == "TH"
    assert scene.actors[2].name == "MOs"
    assert scene.actors[3].name == "CA1"

    root_bounds = scene.root.bounds()
    th_bounds = th.bounds()
    mos_bounds = brain_regions[0].bounds()
    ca1_bounds = brain_regions[1].bounds()

    check_bounds(th_bounds, root_bounds)
    check_bounds(mos_bounds, root_bounds)
    check_bounds(ca1_bounds, root_bounds)


def test_brainglobe_atlas():
    scene = Scene(atlas_name="example_mouse_100um", title="example_mouse")

    scene.render(interactive=False)

    assert len(scene.actors) == 2
    assert scene.actors[0].name == "root"
    assert scene.actors[1].name == "title"
    assert scene.atlas.atlas_name == "example_mouse_100um"


def test_cell_density(scene):
    mos = scene.add_brain_region("MOs", alpha=0.0)
    coordinates = get_n_points_in_region(mos, 2000)

    points = Points(coordinates, name="CELLS", colors="salmon")
    points_density = PointsDensity(coordinates)
    scene.add(points)
    scene.add(points_density)

    scene.render(interactive=False)

    assert scene.actors[1] == mos
    assert scene.actors[2] == points
    assert scene.actors[3] == points_density

    root_bounds = scene.root.bounds()
    points_bounds = points.bounds()
    points_density_bounds = points_density.bounds()

    check_bounds(points_bounds, root_bounds)
    check_bounds(points_density_bounds, root_bounds)


def test_gene_expression(scene):
    gene = "Gpr161"
    geapi = GeneExpressionAPI()
    expids = geapi.get_gene_experiments(gene)
    data = geapi.get_gene_data(gene, expids[1])

    gene_actor = geapi.griddata_to_volume(
        data, min_quantile=99, cmap="inferno"
    )
    ca1 = scene.add_brain_region("CA1", alpha=0.2, color="skyblue")
    act = scene.add(gene_actor)

    scene.render(interactive=False)

    # Expand bounds by 500 px
    ca1_bounds = ca1.bounds()
    expanded_bounds = [
        bound - 500 if i % 2 == 0 else bound + 500
        for i, bound in enumerate(ca1_bounds)
    ]

    gene_actor_bounds = act.bounds()

    assert scene.actors[1] == ca1
    assert scene.actors[2] == act

    check_bounds(gene_actor_bounds, expanded_bounds)


def test_neurons(scene, pytestconfig):
    root_path = pytestconfig.rootpath

    neuron = Neuron(root_path / "tests" / "files" / "neuron1.swc")
    scene.add(neuron)
    scene.render(interactive=False)

    assert len(scene.actors) == 2
    assert scene.actors[1].name == "neuron1.swc"

    neuron_bounds = scene.actors[1].bounds()
    # Based on pre-calculated bounds of this specific neuron
    expected_bounds = (2177, 7152, 2319, 5056, -9147, -1294)

    check_bounds(neuron_bounds, expected_bounds)


def test_ruler(scene):
    th, mos = scene.add_brain_region("TH", "MOs", alpha=0.3)
    p1 = th.center_of_mass()
    p2 = mos.center_of_mass()

    rul1 = ruler(p1, p2, unit_scale=0.01, units="mm")
    rul2 = ruler_from_surface(p1, scene.root, unit_scale=0.01, units="mm")

    scene.add(rul1, rul2)

    scene.render(interactive=False)

    assert len(scene.actors) == 5
    assert scene.actors[1] == th
    assert scene.actors[2] == mos
    assert scene.actors[3] == rul1
    assert scene.actors[4] == rul2

    root_bounds = scene.root.bounds()
    th_bounds = th.bounds()
    mos_bounds = mos.bounds()
    rul1_bounds = rul1.bounds()
    rul2_bounds = rul2.bounds()

    check_bounds(th_bounds, root_bounds)
    check_bounds(mos_bounds, root_bounds)
    check_bounds(rul1_bounds, root_bounds)
    check_bounds(rul2_bounds, root_bounds)


def test_screenshot(scene, pytestconfig):
    scene.add_brain_region("TH")

    scene.render(interactive=False)
    scene.screenshot(name="test_screenshot", scale=2)
    screenshot_path = Path.cwd() / "test_screenshot.png"

    assert screenshot_path.exists()

    screenshot_path.unlink()


def test_slice(scene):
    th, mos, ca1 = scene.add_brain_region(
        "TH", "MOs", "CA1", alpha=0.2, color="green"
    )
    th_clone = th._mesh.clone()
    mos_clone = mos._mesh.clone()
    ca1_clone = ca1._mesh.clone()

    scene.slice("frontal", actors=[mos])
    plane = scene.atlas.get_plane(pos=mos.center_of_mass(), norm=(1, 1, 2))
    scene.slice(plane, actors=[ca1])
    scene.render(interactive=False)

    assert th_clone.bounds() == th.bounds()
    assert mos_clone.bounds() != mos.bounds()
    assert ca1_clone.bounds() != ca1.bounds()


@pytest.mark.slow
@pytest.mark.local
def test_user_volumetric_data():
    scene = Scene(atlas_name="mpin_zfish_1um")
    retrieved_paths = pooch.retrieve(
        url="https://api.mapzebrain.org/media/Lines/brn3cGFP/average_data/T_AVG_s356tTg.zip",
        known_hash="54b59146ba08b4d7eea64456bcd67741db4b5395235290044545263f61453a61",
        path=Path.home()
        / ".brainglobe"
        / "brainrender-example-data",  # zip will be downloaded here
        progressbar=True,
        processor=pooch.Unzip(
            extract_dir=""
            # path to unzipped dir,
            # *relative* to the path set in 'path'
        ),
    )

    datafile = Path(retrieved_paths[1])  # [0] is zip file
    data = imio.load.load_any(datafile)
    source_space = AnatomicalSpace("ira")
    target_space = scene.atlas.space
    transformed_data = source_space.map_stack_to(target_space, data)

    vol = VedoVolume(transformed_data).smooth_median()

    mesh = vol.isosurface(value=20).decimate().clean()
    SHIFT = [30, 15, -20]  # fine tune mesh position
    current_position = mesh.pos()
    new_position = [SHIFT[i] + current_position[i] for i in range(3)]
    mesh.pos(*new_position)

    scene.add(mesh)
    scene.render(interactive=False)

    assert len(scene.actors) == 2

    root_bounds = scene.root.bounds()
    mesh_bounds = scene.actors[1].bounds()

    # Have to expand root bounds by 20 px

    expanded_bounds = [
        bound - 20 if i % 2 == 0 else bound + 20
        for i, bound in enumerate(root_bounds)
    ]

    check_bounds(mesh_bounds, expanded_bounds)


def test_video(scene, pytestconfig):
    root_path = pytestconfig.rootpath
    video_directory = root_path / "tests" / "videos"

    scene.add_brain_region("TH")
    vm = VideoMaker(scene, video_directory, "vid1")
    vm.make_video(elevation=2, duration=2, fps=15)
    video_path = video_directory / "vid1.mp4"

    assert video_directory.exists()
    assert video_path.exists()

    video_path.unlink()
    Path.rmdir(video_directory)


def test_volumetric_data(scene, pytestconfig):
    root_path = pytestconfig.rootpath
    data = np.load(root_path / "tests" / "files" / "volume.npy")
    actor = Volume(
        data,
        voxel_size=200,
        as_surface=False,
        c="Reds",
    )
    scene.add(actor)
    scene.render(interactive=False)

    assert len(scene.actors) == 2
    assert scene.actors[1] == actor

    root_bounds = scene.root.bounds()
    actor_bounds = actor.bounds()

    # Have to expand root bounds by 450 px
    expanded_bounds = [
        bound - 550 if i % 2 == 0 else bound + 550
        for i, bound in enumerate(root_bounds)
    ]

    check_bounds(actor_bounds, expanded_bounds)
