from brainrender import settings
import pytest

settings.INTERACTIVE = False


@pytest.mark.slow
@pytest.mark.local
def test_examples():
    import examples

    examples.add_cells
    examples.add_mesh_from_file
    examples.animation
    examples.brain_regions
    examples.brainglobe_atlases
    examples.cell_density
    examples.custom_camera
    examples.gene_expression
    examples.neurons
    examples.ruler
    examples.settings
    examples.slice
    examples.streamlines
    examples.user_volumetric_data
    examples.video
    examples.volumetric_data
