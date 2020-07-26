import pytest
from brainrender.atlases.custom_atlases.insects_brains_db import IBDB
from brainrender.scene import Scene


@pytest.fixture
def scene():
    return Scene(
        atlas=IBDB,  # specify that we are using the insects brains databse atlas
        atlas_kwargs=dict(
            species="Schistocerca gregaria"
        ),  # Specify which insect species' brain to use
    )


def test_ibdb(scene):
    print(scene.atlas.species_info)

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
    scene.add_brain_regions("PB", colors="red", use_original_color=False)
    scene.add_brain_regions("PB", colors=["red"], use_original_color=False)


def test_root(scene):
    scene.atlas.make_root_mesh()
