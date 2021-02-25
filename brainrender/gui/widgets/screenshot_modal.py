from qtpy.QtWidgets import QDialog, QLabel, QVBoxLayout
from qtpy import QtCore

from brainrender.gui.style import style, update_css


class ScreenshotModal(QDialog):
    left = 250
    top = 250
    width = 400
    height = 120

    def __init__(self, main_window, palette):
        """
        Creates a new window for user to input
        which regions to add to scene.

        Arguments:
        ----------

        main_window: reference to the App's main window
        palette: main_window's palette, used to style widgets
        """
        super().__init__()
        self.setWindowTitle("Add brain regions")
        self.ui()
        self.main_window = main_window
        self.setStyleSheet(update_css(style, palette))

        # Start timer to autoclose
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(1500)
        self.timer.timeout.connect(self.close)
        self.timer.start()

    def ui(self):
        """
        Define UI's elements
        """
        self.setGeometry(self.left, self.top, self.width, self.height)

        layout = QVBoxLayout()

        label = QLabel(self)

        label.setStyleSheet("font-size: 18pt; font-weight: 700;")

        label.setObjectName("PopupLabel")
        label.setText("Screenshot saved")
        layout.addWidget(label)

        self.setLayout(layout)
        self.setModal(True)
        self.show()
