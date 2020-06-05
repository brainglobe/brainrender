import pandas as pd
from morphapi.api.mouselight import MouseLightAPI
from random import choices
from tqdm import tqdm
import time
import numpy as np

from vtkplotter import Text

from brainrender.scene import Scene
from brainrender.atlases.mouse import ABA
from brainrender.Utils.camera import (
    buildcam,
    sagittal_camera,
    top_camera,
    coronal_camera,
)
from brainrender.colors import colorMap, makePalette
from brainrender.atlases.insects_brains_db import IBDB
from brainrender.morphology.visualise import MorphologyScene

# ---------------------------------------------------------------------------- #
#                               Basic scene elems                              #
# ---------------------------------------------------------------------------- #


def test_regions():
    scene = Scene(camera=coronal_camera)
    regions = ["MOs", "VISp", "ZI"]
    scene.add_brain_regions(regions, colors="green")
    ca1 = scene.add_brain_regions("CA1", wireframe=True)
    ca1.alpha(0.2)
    scene.close()


def test_camera():
    # Create a scene
    scene = Scene(camera="top")  # specify that you want a view from the top

    # render
    scene.render(interactive=False,)
    scene.close()

    # Now render but with a different view
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

    scene.render(interactive=False, camera=bespoke_camera, zoom=1)
    scene.close()


def test_labelled_cells():
    # Create a scene
    scene = Scene()  # specify that you want a view from the top

    # Gerate the coordinates of N cells across 3 regions
    regions = ["MOs", "VISp", "ZI"]
    N = 1000  # getting 1k cells per region, but brainrender can deal with >1M cells easily.

    # Render regions
    scene.add_brain_regions(regions, alpha=0.2)

    # Get fake cell coordinates
    cells = []  # to store x,y,z coordinates
    for region in regions:
        region_cells = scene.get_n_random_points_in_region(region=region, N=N)
        cells.extend(region_cells)
    x, y, z = (
        [c[0] for c in cells],
        [c[1] for c in cells],
        [c[2] for c in cells],
    )
    cells = pd.DataFrame(dict(x=x, y=y, z=z))

    # Add cells
    scene.add_cells(cells, color="darkseagreen", res=12, radius=25)


def test_scene_title():
    scene = Scene(title="The thalamus.")
    scene.render(interactive=False)
    scene.close()


def test_text_3d():
    # Crate a scene
    scene = Scene(
        add_root=False, display_inset=False, use_default_key_bindings=False
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

        # Add letter and silhouette to the scne
        act = Text(
            letter, depth=0.5, c=colors[n], pos=(x, 0, 0), justify="centered"
        )
        sil = act.silhouette().lw(3).color("k")
        scene.add_vtkactor(act, sil)

    scene.render(interactive=False)
    scene.close()


def text_actor_labels():
    # Create a scene
    scene = Scene()

    # add_brain_regions can be used to add labels directly
    scene.add_brain_regions("VAL", add_labels=True)

    # you can also use scene.add_actor_label
    mos = scene.add_brain_regions("MOs")

    # Add another label, this time make it gray and shift it slightly
    scene.add_actor_label(
        mos, "MOs", size=400, color="blackboard", xoffset=250
    )


def test_crosshair():
    scene = Scene()
    scene.add_brain_regions("TH", use_original_color=False, alpha=0.4)

    # Add a point in the right hemisphere
    point = scene.atlas.get_region_CenterOfMass("TH")
    scene.add_crosshair_at_point(
        point,
        ap=False,  # show only lines on the medio-lateral and dorso-ventral axes
        point_kwargs={
            "color": "salmon"
        },  # specify how the point at the center of the crosshair looks like
    )

    # Add a point in the left hemisphere
    point = scene.atlas.get_region_CenterOfMass("TH", hemisphere="left")
    scene.add_crosshair_at_point(
        point,
        ap=False,  # show only lines on the medio-lateral and dorso-ventral axes
        point_kwargs={
            "color": "darkseagreen"
        },  # specify how the point at the center of the crosshair looks like
    )


def test_cut_with_plane():
    scene = Scene(use_default_key_bindings=True)

    # Add some actors
    root = scene.actors["root"]
    scene.add_brain_regions(["STR", "TH"], alpha=0.5)

    # Specify position, size and orientation of the plane
    pos = scene.atlas._root_midpoint
    sx, sy = 15000, 15000
    norm = [0, 1, 1]
    plane = scene.atlas.get_plane_at_point(
        pos, norm, sx, sy, color="lightblue"
    )

    # Cut
    scene.cut_actors_with_plane(
        plane,
        close_actors=False,  # set close_actors to True close the holes left by cutting
        showplane=True,
        actors=scene.actors["root"],
    )

    sil = root.silhouette().lw(1).c("k")
    scene.add_vtkactor(sil)


def test_add_plane():
    scene = Scene(add_root=False, display_inset=False)
    scene.add_plane("sagittal")


# ---------------------------------------------------------------------------- #
#                                Mouse specific                                #
# ---------------------------------------------------------------------------- #


def test_streamlines():
    scene = Scene()

    filepaths, data = scene.atlas.download_streamlines_for_region("CA1")

    scene.add_brain_regions(["CA1"], use_original_color=True, alpha=0.2)

    scene.add_streamlines(
        data, color="darkseagreen", show_injection_site=False
    )

    scene.render(camera="sagittal", zoom=1, interactive=False)
    scene.close()


def test_streamlines_colored():
    # Start by creating a scene with the allen brain atlas atlas
    scene = Scene()

    # Download streamlines data for injections in the CA1 field of the hippocampus
    filepaths, data = scene.atlas.download_streamlines_for_region("CA1")

    scene.add_brain_regions(["CA1"], use_original_color=True, alpha=0.2)

    # you can pass either the filepaths or the data
    colors = makePalette(len(data), "salmon", "lightgreen")
    scene.add_streamlines(data, color=colors, show_injection_site=False)


def test_neurons():
    scene = Scene()

    mlapi = MouseLightAPI()

    # Fetch metadata for neurons with some in the secondary motor cortex
    neurons_metadata = mlapi.fetch_neurons_metadata(
        filterby="soma", filter_regions=["MOs"]
    )

    # Then we can download the files and save them as a .json file
    neurons = mlapi.download_neurons(neurons_metadata[:5])
    scene.add_neurons(
        neurons, color="salmon", display_axon=False, neurite_radius=6
    )


def test_tractography():
    scene = Scene()
    analyzer = ABA()
    p0 = scene.atlas.get_region_CenterOfMass("ZI")
    tract = analyzer.get_projection_tracts_to_target(p0=p0)
    scene.add_tractography(tract, color_by="target_region")

    scene = Scene()
    scene.add_tractography(
        tract, color_by="target_region", VIP_regions=["SCm"], VIP_color="green"
    )


# ---------------------------------------------------------------------------- #
#                                Custom atlases                                #
# ---------------------------------------------------------------------------- #
def test_ibdb():
    scene = Scene(
        atlas=IBDB,  # specify that we are using the insects brains databse atlas
        atlas_kwargs=dict(
            species="Schistocerca gregaria"
        ),  # Specify which insect species' brain to use
    )

    # You can use print(scene.atlas.species_info) to see a list of available species

    # Print the hierarchical organisation of brain regions in the atlas:
    print(scene.atlas.structures_hierarchy)

    # Now print some of the structures names [used to fetch mesh data]
    print(scene.atlas.structures.head())

    # Add some brain regions in the mushroom body to the rendering
    central_complex = [
        "CBU-S2",
        "CBU-S1",
        "CBU-S3",
        "NO-S3_left",
        "NO-S2_left",
        "NO-S2_right",
        "NO-S3_right",
        "NO_S1_left",
        "NO-S1_right",
        "NO-S4_left",
        "NO-S4_right",
        "CBL",
        "PB",
    ]

    scene.add_brain_regions(central_complex, alpha=1)


# ---------------------------------------------------------------------------- #
#                                  Morphology                                  #
# ---------------------------------------------------------------------------- #
def test_morphology_scene():

    scene = MorphologyScene(title="A neuron")

    scene.add_neurons(
        "Examples/example_files/neuron4.swc",
        color=dict(soma="red", dendrites="orangered", axon=[0.4, 0.4, 0.4],),
    )


# ---------------------------------------------------------------------------- #
#                                   Animation                                  #
# ---------------------------------------------------------------------------- #


def test_animated_scene():
    # --------------------------------- Variables -------------------------------- #
    minalpha = 0.01  # transparency of background neurons
    darkcolor = "lightgray"  # background neurons color

    N_FRAMES = 50
    N_neurons = 10  # number of neurons to show in total, if -1 all neurons are shown but it might take a while to render them at first
    N_neurons_in_frame = (
        2  # number of neurons to be highlighted in a given frame
    )
    N_frames_for_change = 15  # every N frames which neurons are shown changes

    # Variables to specify camera position at each frame
    zoom = np.linspace(1, 1.5, N_FRAMES)
    frac = np.zeros_like(
        zoom
    )  # for camera transition, interpolation value between cameras
    frac[:150] = np.linspace(0, 1, 150)
    frac[150:] = np.linspace(1, 0, len(frac[150:]))

    # -------------------------------- Fetch data -------------------------------- #

    # Then we can download the files and save them as a .json file
    ml_api = MouseLightAPI()
    # Fetch metadata for neurons with some in the secondary motor cortex
    neurons_metadata = ml_api.fetch_neurons_metadata(
        filterby="soma", filter_regions=["MOs"]
    )

    neurons_files = ml_api.download_neurons(neurons_metadata[:N_neurons])

    # ------------------------------- Create scene ------------------------------- #
    scene = Scene(display_inset=False, use_default_key_bindings=True)
    scene.actors["root"]

    scene.add_neurons(
        neurons_files, random_color=True, neurite_radius=12, alpha=0
    )

    # Make all neurons background
    for neuron in scene.actors["neurons"]:
        for mesh in neuron.values():
            mesh.alpha(minalpha)
            mesh.color(darkcolor)

    # Create new cameras
    cam1 = buildcam(sagittal_camera)

    cam2 = buildcam(
        dict(
            position=[-16624.081, -33431.408, 33527.412],
            focal=[6587.835, 3849.085, 5688.164],
            viewup=[0.634, -0.676, -0.376],
            distance=51996.653,
            clipping=[34765.671, 73812.327],
        )
    )

    cam3 = buildcam(
        dict(
            position=[1862.135, -4020.792, -36292.348],
            focal=[6587.835, 3849.085, 5688.164],
            viewup=[0.185, -0.97, 0.161],
            distance=42972.44,
            clipping=[29629.503, 59872.10],
        )
    )

    # ------------------------------- Create frames ------------------------------ #
    # Create frames
    prev_neurons = []
    for step in tqdm(np.arange(N_FRAMES)):
        if step % N_frames_for_change == 0:  # change neurons every N framse

            # reset neurons from previous set of neurons
            for neuron in prev_neurons:
                for component, actor in neuron.items():
                    actor.alpha(minalpha)
                    actor.color(darkcolor)
            prev_neurons = []

            # highlight new neurons
            neurons = choices(scene.actors["neurons"], k=N_neurons_in_frame)
            for n, neuron in enumerate(neurons):
                color = colorMap(
                    n, "Greens_r", vmin=-2, vmax=N_neurons_in_frame + 3
                )
                for component, actor in neuron.items():
                    actor.alpha(1)
                    actor.color(color)
                prev_neurons.append(neuron)

        # Move scene camera between 3 cameras
        scene.plotter.moveCamera(cam1, cam2, frac[step])
        if frac[step] == 1:
            cam1 = cam3

        # Update rendered window
        time.sleep(0.1)
        scene.render(zoom=zoom[step], interactive=False, video=True)
    scene.close()


def test_video():
    from brainrender.animation.video import BasicVideoMaker as VideoMaker

    scene = Scene()

    # Create an instance of VideoMaker with our scene
    vm = VideoMaker(scene, niters=10)

    # Make a video!
    vm.make_video(
        elevation=1, roll=5
    )  # specify how the scene rotates at each frame


def test_custom_video():
    from brainrender.animation.video import CustomVideoMaker

    # --------------------------------- Variables -------------------------------- #
    minalpha = 0  # transparency of background neurons
    darkcolor = "lightgray"  # background neurons color

    N_FRAMES = 20
    N_streamlines_in_frame = (
        2  # number of streamlines to be highlighted in a given frame
    )
    N_frames_for_change = (
        50  # every N frames which streamlines are shown changes
    )

    # Variables to specify camera position at each frame
    zoom = np.linspace(1, 1.35, N_FRAMES)
    frac = np.zeros_like(
        zoom
    )  # for camera transition, interpolation value between cameras
    frac[:150] = np.linspace(0, 1, 150)
    frac[150:] = np.linspace(1, 0, len(frac[150:]))

    # ------------------------------- Create scene ------------------------------- #
    scene = Scene(display_inset=True, use_default_key_bindings=True)

    filepaths, data = scene.atlas.download_streamlines_for_region("TH")
    scene.add_streamlines(
        data, color="darkseagreen", show_injection_site=False
    )

    scene.add_brain_regions(["TH"], alpha=0.2)

    # Make all streamlines background
    for mesh in scene.actors["tracts"]:
        mesh.alpha(minalpha)
        mesh.color(darkcolor)

    # Create new cameras
    cam1 = buildcam(sagittal_camera)
    cam2 = buildcam(top_camera)
    cam3 = buildcam(
        dict(
            position=[1862.135, -4020.792, -36292.348],
            focal=[6587.835, 3849.085, 5688.164],
            viewup=[0.185, -0.97, 0.161],
            distance=42972.44,
            clipping=[29629.503, 59872.10],
        )
    )

    # Iniziale camera position
    scene.plotter.moveCamera(cam1, cam2, frac[0])

    # ------------------------------- Create frames ------------------------------ #
    def frame_maker(scene=None, video=None, videomaker=None):
        prev_streamlines = []
        for step in tqdm(np.arange(N_FRAMES)):
            if (
                step % N_frames_for_change == 0
            ):  # change neurons every N framse

                # reset neurons from previous set of neurons
                for mesh in prev_streamlines:
                    mesh.alpha(minalpha)
                    mesh.color(darkcolor)
                prev_streamlines = []

                # highlight new neurons
                streamlines = choices(
                    scene.actors["tracts"], k=N_streamlines_in_frame
                )
                for n, mesh in enumerate(streamlines):
                    # color = colorMap(n, 'Reds', vmin=-2, vmax=N_streamlines_in_frame+3)
                    mesh.alpha(0.7)
                    mesh.color("orangered")
                    prev_streamlines.append(mesh)

            # Move scene camera between 3 cameras
            if step < 150:
                scene.plotter.moveCamera(cam1, cam2, frac[step])
            else:
                scene.plotter.moveCamera(cam3, cam2, frac[step])

            # Add frame to video
            scene.render(zoom=zoom[step], interactive=False, video=True)
            video.addFrame()
        return video

    # ---------------------------------------------------------------------------- #
    #                                  Video maker                                 #
    # ---------------------------------------------------------------------------- #
    vm = CustomVideoMaker(scene, save_name="streamlines_animation")
    vm.make_video(frame_maker)
