import requests

# ----------------------------- Internet queries ----------------------------- #


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


def send_query(query_string, clean=False):
    """
    Send a query/request to a website

    :param query_string: string with query content
    :param clean:  (Default value = False)

    """
    response = requests.get(query_string)
    if response.ok:
        if not clean:
            return response.json()["msg"]
        else:
            return response.json()
    else:
        raise ValueError("Invalide query string: {}".format(query_string))


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
