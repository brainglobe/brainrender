from pathlib import Path
from brainrender.Utils.webqueries import connected_to_internet


def fail_on_no_connection(func):
    if not connected_to_internet():
        raise ConnectionError("No internet connection found.")

    def inner(*args, **kwargs):
        return func(*args, **kwargs)

    return inner


def check_file_exists(func):
    def inner(*args, **kwargs):
        if not Path(args[0]).exists():
            raise FileNotFoundError(f"File {args[0]} not found")
        return func(*args, **kwargs)

    return inner
