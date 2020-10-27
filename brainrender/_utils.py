def listify(obj):
    """
        makes sure that the obj is a list
    """
    if isinstance(obj, list):
        return obj
    elif isinstance(obj, tuple):
        return list(obj)
    else:
        return [obj]


def return_list_smart(lst):
    """
        If the list has length > returns the list
        if it has length == 1 it returns the element
        if it has length == 0 it returns None
    """
    if len(lst) > 1:
        return lst
    elif len(lst) == 1:
        return lst[0]
    else:
        return None
