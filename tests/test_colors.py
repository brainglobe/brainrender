from brainrender._colors import map_color, make_palette, get_random_colors
import pytest


@pytest.mark.parametrize(
    "value, name, vmin, vmax",
    [(1, "jet", 0, 2), (1, "jet", 0, -2), (1, "Blues", 0, 2)],
)
def test_cmap(value, name, vmin, vmax):
    if vmax < vmin:
        with pytest.raises(ValueError):
            col = map_color(value, name=name, vmin=vmin, vmax=vmax)
    else:
        col = map_color(value, name=name, vmin=vmin, vmax=vmax)
        assert len(col) == 3


@pytest.mark.parametrize(
    "N, colors",
    [
        (5, ("salmon", "green", "blue", "red", "magenta", "black")),
        (1, ("salmon", "red")),
        (3, ("salmon", "blue")),
    ],
)
def test_make_palette(N, colors):
    if len(colors) > N:
        with pytest.raises(ValueError):
            cols = make_palette(N, *colors)
    else:
        cols = make_palette(N, *colors)
        if N == 1:
            assert len(set(cols)) == 1
        assert len(cols) == N


@pytest.mark.parametrize("n", [(1), (2), (5)])
def test_get_random_colors(n):
    cols = get_random_colors(n_colors=n)
    if n == 1:
        assert isinstance(cols, str)
    else:
        assert len(cols) == n
