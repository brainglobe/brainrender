"""File I/O and network utilities for brainrender."""

from collections.abc import Callable
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

import requests
from vedo import load, Mesh, Volume

P = ParamSpec("P")
R = TypeVar("R")


def connected_to_internet(
    url: str = "http://www.google.com/",
    timeout: int = 5,
) -> bool:
    """
    Check that there is an internet connection.

    Parameters
    ----------
    url
        URL to use for testing. Default ``"http://www.google.com/"``.
    timeout
        Timeout in seconds. Default 5.

    Returns
    -------
    bool
        ``True`` if an internet connection is available, otherwise ``False``.
    """

    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:  # pragma: no cover
        print("No internet connection available.")  # pragma: no cover
    return False


def fail_on_no_connection(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator that raises an error if no internet connection is available.

    Parameters
    ----------
    func
        Function to wrap.

    Returns
    -------
    collections.abc.Callable

    Raises
    ------
    ConnectionError
        If no internet connection is found.
    """
    if not connected_to_internet():  # pragma: no cover
        raise ConnectionError(
            "No internet connection found."
        )  # pragma: no cover

    def inner(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return inner


def request(url: str) -> requests.Response:
    """
    Send a GET request to a URL.

    Parameters
    ----------
    url
        URL to request.

    Returns
    -------
    requests.Response

    Raises
    ------
    ConnectionError
        If no internet connection is found.
    ValueError
        If the request fails.
    """
    if not connected_to_internet():  # pragma: no cover
        raise ConnectionError(
            "No internet connection found."
        )  # pragma: no cover

    response = requests.get(url)
    if response.ok:
        return response
    else:  # pragma: no cover
        exception_string = "URL request failed: {}".format(
            response.reason
        )  # pragma: no cover
    raise ValueError(exception_string)


def check_file_exists(func: Callable[P, R]) -> Callable[P, R]:  # pragma: no cover
    """
    Decorator that raises an error if a function's first argument
    is not a path to an existing file.

    Parameters
    ----------
    func
        Function to wrap.

    Returns
    -------
    collections.abc.Callable

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """

    def inner(*args: Any, **kwargs: Any) -> Any:
        if not Path(args[0]).exists():
            raise FileNotFoundError(
                f"File {args[0]} not found"
            )  # pragma: no cover
        return func(*args, **kwargs)

    return inner


@check_file_exists
def load_mesh_from_file(
    filepath: str | Path,
    color: str | None = None,
    alpha: float | None = None,
) -> Mesh | Volume:
    """
    Load a mesh or volume from a file (e.g. .obj, .stl).

    Parameters
    ----------
    filepath
        Path to the mesh file.
    color
        Colour to apply to the mesh.
    alpha
        Transparency to apply to the mesh.

    Returns
    -------
    vedo.Mesh or vedo.Volume
    """
    actor = load(str(filepath))
    actor.c(color).alpha(alpha)
    return actor


def convert_meshio_to_vedo(meshio_mesh, color=None, alpha=None):
    """
    Convert a meshio mesh to a vedo mesh.

    Parameters
    ----------
    meshio_mesh : meshio.Mesh
        The meshio mesh to convert.
    color : str, optional
        The color to apply to the mesh. Default is None.
    alpha : float, optional
        The transparency to apply to the mesh. Default is None.

    Returns
    -------
    vedo.Mesh
        The converted vedo mesh.
    """
    actor = Mesh([meshio_mesh.points, meshio_mesh.cells_dict["triangle"]])
    actor.c(color).alpha(alpha)
    return actor
