from brainrender._utils import listdir, get_subdirs, listify, return_list_smart


def test_listdir():
    items = listdir("test")
    assert isinstance(items, list)


def test_get_subdirs():
    subs = get_subdirs("brainrender")
    assert isinstance(subs, list)


def test_listify():
    assert isinstance(listify([1, 2, 3]), list)
    assert isinstance(listify((1, 2, 3)), list)
    assert isinstance(listify(1), list)


def test_return_list_smart():
    l1 = [1, 2, 3]
    assert isinstance(return_list_smart(l1), list)
    assert return_list_smart([]) is None
