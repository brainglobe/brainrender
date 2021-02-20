from qtpy.QtWidgets import QDialog, QLineEdit, QPushButton, QLabel, QVBoxLayout
from brainrender.gui.style import style, update_css


class AddFromFileWindow(QDialog):
    left = 250
    top = 250
    width = 400
    height = 300

    label_msg = (
        "Write the acronyms of brainregions  "
        + "you wish to add.\n[as 'space' separated strings (e.g.: STN TH)]"
    )

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

    def ui(self):
        """
        Define UI's elements
        """
        self.setGeometry(self.left, self.top, self.width, self.height)

        layout = QVBoxLayout()

        # Alpha
        alpha_label = QLabel(self)
        alpha_label.setObjectName("PopupLabel")
        alpha_label.setText("Alpha")

        self.alpha_textbox = QLineEdit(self)
        self.alpha_textbox.setText(str(1.0))

        # Color
        color_label = QLabel(self)
        color_label.setObjectName("PopupLabel")
        color_label.setText("Color")

        self.color_textbox = QLineEdit(self)
        self.color_textbox.setText("default")

        # Create a button in the window
        self.button = QPushButton("Ok", self)
        self.button.clicked.connect(self.on_click)
        self.button.setObjectName("RegionsButton")

        layout.addWidget(alpha_label)
        layout.addWidget(self.alpha_textbox)

        layout.addWidget(color_label)
        layout.addWidget(self.color_textbox)

        layout.addWidget(self.button)

        self.setLayout(layout)
        self.show()

    def on_click(self):
        """
        On click or 'Enter' get the regions
        from the input and call the add_regions
        method of the main window
        """
        self.close()
