from brainrender import settings
import pytest

settings.INTERACTIVE = False


@pytest.mark.slow
def test_examples():
    import examples

    examples.brain_regions
