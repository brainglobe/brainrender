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
    except requests.ConnectionError:
        print("No internet connection available.")
    return False


def fail_on_no_connection(func):
    if not connected_to_internet():
        raise ConnectionError("No internet connection found.")

    def inner(*args, **kwargs):
        return func(*args, **kwargs)

    return inner


@fail_on_no_connection
def request(url):
    """
    Sends a request to a url

    :param url: 

    """
    response = requests.get(url)
    if response.ok:
        return response
    else:
        exception_string = "URL request failed: {}".format(response.reason)
    raise ValueError(exception_string)


def check_file_exists(func):
    def inner(*args, **kwargs):
        if not Path(args[0]).exists():
            raise FileNotFoundError(f"File {args[0]} not found")
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
