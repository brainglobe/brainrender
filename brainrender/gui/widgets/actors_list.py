from qtpy.QtGui import QIcon
from pkg_resources import resource_filename
from loguru import logger


def get_in_alist(qlist):
    """
    Gets items in the actor list
    """
    items = []
    for index in range(qlist.count()):
        items.append(qlist.item(index).text())
    return items


def update_actors_list(qlist, actorsdict):
    """
    Adds missing entries in the actors list
    """
    listed = get_in_alist(qlist)

    # Add items to list
    for actor in actorsdict.keys():
        if actor not in listed:
            qlist.insertItem(qlist.count() + 1, actor)

            item = qlist.item(qlist.count() - 1)
            item.setIcon(
                QIcon(resource_filename("brainrender.gui", "icons/eye.svg"))
            )


def remove_from_list(qlist, aname):
    """
    Removes an entry from the actors list
    """
    logger.debug(f"GUI: removing {aname} from actors list")
    if aname not in get_in_alist(qlist):
        raise ValueError(
            f"Attempting to remove {aname} from list, but {aname} not in list."
        )
    else:
        idx = [n for n, a in enumerate(get_in_alist(qlist)) if a == aname][0]
        qlist.takeItem(idx)
