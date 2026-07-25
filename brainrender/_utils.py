"""General utility helpers for file system traversal and list manipulation."""

from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


def listdir(fld: str | Path) -> list[str]:
    """
    List the files into a folder with the complete file path instead of the relative file path like os.listdir.

    Parameters
    ----------
    fld
        Path to the folder.

    Returns
    -------
    list of str
    """
    return [str(f) for f in Path(fld).glob("**/*") if f.is_file()]


def get_subdirs(folderpath: str | Path) -> list[str]:
    """
    Return all subdirectories in a given folder.

    Parameters
    ----------
    folderpath
        Path to the folder.

    Returns
    -------
    list of str
    """
    return [str(f) for f in Path(folderpath).glob("**/*") if f.is_dir()]


def listify(obj: T | list[T] | tuple[T, ...]) -> list[T]:
    """
    Ensure the object is a list.

    Parameters
    ----------
    obj
        Object to listify.

    Returns
    -------
    list
    """
    if isinstance(obj, list):
        return obj
    elif isinstance(obj, tuple):
        return list(obj)
    else:
        return [obj]


def return_list_smart(lst: list[T]) -> list[T] | T | None:
    """
    Return a list, single element, or None depending on list length.

    Parameters
    ----------
    lst
        Input list.

    Returns
    -------
    list, Any, or None
        The list if length > 1, the single item if length == 1,
        or None if empty.
    """
    if len(lst) > 1:
        return lst
    elif len(lst) == 1:
        return lst[0]
    else:
        return None
