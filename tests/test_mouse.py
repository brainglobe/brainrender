import pytest
from vedo import Mesh
import numpy as np

from brainrender.scene import Scene
from brainrender.colors import makePalette
from morphapi.api.mouselight import MouseLightAPI
from brainrender.ABA.gene_expression import GeneExpressionAPI


@pytest.fixture
def scene():
    return Scene()


def test_gene_expression():
    geapi = GeneExpressionAPI()
    gene = "Cacna2d1"
    geneid = geapi.get_gene_id_by_name(gene)
    symbol = geapi.get_gene_symbol_by_id(geneid)

    expids = geapi.get_gene_experiments(geneid)
    if not isinstance(geneid, int):
        raise ValueError
    if symbol != gene:
        raise ValueError
    if not isinstance(expids, list) or not len(expids):
        raise ValueError
    if not isinstance(expids[0], int):
        raise ValueError

    data = geapi.get_gene_data(geneid, expids[0])
    data3 = geapi.get_gene_data(
        geneid, expids[0]
    )  # again to make sure cache works
    data2 = geapi.get_gene_data(geneid, expids[1])

    if (
        not isinstance(data, np.ndarray)
        or not isinstance(data2, np.ndarray)
        or not isinstance(data3, np.ndarray)
    ):
        raise ValueError
    if not np.array_equal(data, data3):
        raise ValueError

    gene_actor = geapi.griddata_to_volume(
        data, min_quantile=90, cmap="inferno"
    )
    gene_actor2 = geapi.griddata_to_volume(data2, min_value=0.2)

    if not isinstance(gene_actor, Mesh) or not isinstance(gene_actor2, Mesh):
        raise ValueError


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

    neurons = mlapi.download_neurons(neurons_metadata[:2])
    actors = scene.add_neurons(
        neurons,
        color="salmon",
        display_axon=False,
        neurite_radius=6,
        soma_radius=20,
    )

    actor = scene.add_neurons(
        neurons[0], color="salmon", display_axon=False, use_cache=True,
    )
    scene.add_neurons(
        actors, color=None, display_dendrites=False, use_cache=False
    )

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

    scene.add_neurons(actor)


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
