# from qtpy import QtCore
import pytest

from brainrender.gui.app import App


@pytest.mark.local
def test_simple_launch(qtbot):
    window = App()
    qtbot.addWidget(window)
    window.show()


# @pytest.mark.local
# def test_toggle_treeview(qtbot):
#     window = App()
#     qtbot.addWidget(window)
#     window.show()
#     # qtbot.wait_for_window_shown(window)
#     qtbot.mouseClick(
#         window.buttons["show_structures_tree"], QtCore.Qt.LeftButton
#     )
