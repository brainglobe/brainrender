from pathlib import Path
from vedo import load


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
    actor = load(str(filepath)).c(color).alpha(alpha)
    return actor
