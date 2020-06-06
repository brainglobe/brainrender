import pytest
from brainrender.scene import Scene
from brainrender.colors import makePalette
from morphapi.api.mouselight import MouseLightAPI


@pytest.fixture
def scene():
    return Scene()


def test_streamlines(scene):
    filepaths, data = scene.atlas.download_streamlines_for_region("CA1")
    scene.add_streamlines(
        data[0], color="darkseagreen", show_injection_site=False
    )


def test_streamlines_download(scene):
    p0 = scene.atlas.get_region_CenterOfMass("ZI")
    scene.atlas.download_streamlines_to_region(p0)


def test_streamlines_colored(scene):
    filepaths, data = scene.atlas.download_streamlines_for_region("CA1")
    colors = makePalette(len(data), "salmon", "lightgreen")
    scene.add_streamlines(data, color=colors, show_injection_site=False)
    scene.add_streamlines(filepaths, color=None, show_injection_site=True)


def test_neurons(scene):
    mlapi = MouseLightAPI()
    neurons_metadata = mlapi.fetch_neurons_metadata(
        filterby="soma", filter_regions=["MOs"]
    )

    neurons = mlapi.download_neurons(neurons_metadata[:5])
    actors = scene.add_neurons(
        neurons, color="salmon", display_axon=False, neurite_radius=6
    )

    scene.add_neurons(actors, color=None, display_dendrites=False)

    scene.add_neurons(actors, color="Reds", display_dendrites=False)

    scene.add_neurons(
        actors, color=["green" for i in actors], display_dendrites=False
    )

    scene.add_neurons(
        actors, color=dict(soma="red", axon="green", dendrites="blue")
    )

    scene.add_neurons(
        actors,
        color=[
            dict(soma="red", axon="green", dendrites="blue") for i in actors
        ],
    )


def test_tractography(scene):
    p0 = scene.atlas.get_region_CenterOfMass("ZI")

    tract = scene.atlas.get_projection_tracts_to_target(p0=p0)

    scene.add_tractography(tract[:25], color_by="manual", color="red")

    scene.add_tractography(
        tract[25:50],
        color_by="target_region",
        VIP_regions=["SCm"],
        VIP_color="green",
    )

    scene.add_tractography(
        tract[50:75],
        color_by="target_region",
        VIP_regions=["SCm"],
        VIP_color="green",
        include_all_inj_regions=True,
        display_injection_volume=True,
    )
