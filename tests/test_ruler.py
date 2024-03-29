from brainrender import Scene
from brainrender.actors import ruler, ruler_from_surface


def test_ruler():
    s = Scene(title="BR")
    th = s.add_brain_region("TH", hemisphere="left")
    mos = s.add_brain_region("MOs", hemisphere="right")

    s.add(
        ruler(
            th.center_of_mass(),
            mos.center_of_mass(),
            unit_scale=0.01,
            units="mm",
        )
    )

    # s.render(interactive=False)
    del s


def test_ruler_from_surface():
    s = Scene(title="BR")
    th = s.add_brain_region("TH", hemisphere="left")

    s.add(
        ruler_from_surface(
            th.center_of_mass(), s.root, unit_scale=0.01, units="mm"
        )
    )

    # s.render(interactive=False)
    del s
