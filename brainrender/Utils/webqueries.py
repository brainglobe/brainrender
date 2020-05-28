import sys

sys.path.append("./")

from brainrender.Utils.data_io import connected_to_internet

import requests


def request(url):
    """
    Sends a request to a url

    :param url: 

    """
    if not connected_to_internet():
        raise ConnectionError(
            "You need to have an internet connection to send requests."
        )
    response = requests.get(url)
    if response.ok:
        return response
    else:
        exception_string = "URL request failed: {}".format(response.reason)
    raise ValueError(exception_string)
