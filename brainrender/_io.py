from pathlib import Path
from vedo import load
import requests


def connected_to_internet(url="http://www.google.com/", timeout=5):
    """
    Check that there is an internet connection

    :param url: url to use for testing (Default value = 'http://www.google.com/')
    :param timeout:  timeout to wait for [in seconds] (Default value = 5)
    """

    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:  # pragma: no cover
        print("No internet connection available.")  # pragma: no cover
    return False


def fail_on_no_connection(func):
    """
    Decorator that throws an error if no internet connection is available
    """
    if not connected_to_internet():  # pragma: no cover
        raise ConnectionError(
            "No internet connection found."
        )  # pragma: no cover

    def inner(*args, **kwargs):
        return func(*args, **kwargs)

    return inner


def request(url):
    """
    Sends a request to a url

    :param url:

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


def check_file_exists(func):  # pragma: no cover
    """
    Decorator that throws an error if a function;s first argument
    is not a path to an existing file.
    """

    def inner(*args, **kwargs):
        if not Path(args[0]).exists():
            raise FileNotFoundError(
                f"File {args[0]} not found"
            )  # pragma: no cover
        return func(*args, **kwargs)

    return inner


@check_file_exists
def load_mesh_from_file(filepath, color=None, alpha=None):
    """
    Load a a mesh or volume from files like .obj, .stl, ...

    :param filepath: path to file
    :param **kwargs:

    """
    actor = load(str(filepath))
    actor.c(color).alpha(alpha)
    return actor
