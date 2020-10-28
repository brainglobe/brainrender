from brainrender import settings

settings.INTERACTIVE = False


def test_examples():
    import examples

    examples.basic_scene
