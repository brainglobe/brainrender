from qtpy.QtWidgets import (
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QWidget,
    QListWidget,
    QHBoxLayout,
    QLineEdit,
    QTreeView,
    QSplitter,
)
from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy.QtGui import QStandardItemModel
from pkg_resources import resource_filename

from brainrender.gui.style import style, tree_css, update_css, _themes
from brainrender.gui.widgets.tree import StandardItem


class UI(QMainWindow):
    buttons = {}

    right_navbar_button_names = [
        "add brain regions",
        "add cells",
        "add from file",
    ]

    central_column_button_names = [
        "take screenshot",
        "reset",
        "top",
        "side1",
        "side2",
        "front",
    ]

    def __init__(self, theme="dark", **kwargs):
        super().__init__()

        # Get palette
        self.palette = _themes[theme]
        self.theme = theme

        # set the title and icon of main window
        self.setWindowTitle("BRAINGLOBE - brainrender GUI")

        logo_path = resource_filename(
            "brainrender.gui.icons", "BG_logo_mini.svg"
        )
        self.setWindowIcon(QtGui.QIcon(logo_path))

        # set the size of window
        self.Width = 3000
        self.height = int(0.618 * self.Width)
        self.resize(self.Width, self.height)

        # Create UI
        self.get_icons()
        self.initUI()
        self.setStyleSheet(update_css(style, self.palette))

    def get_icons(self):
        """
        Gets the correct path to the icons
        depending on the theme chosen
        """
        self.palette["branch_closed_img"] = resource_filename(
            "brainrender.gui.icons", f"right_{self.theme}.svg"
        )
        self.palette["branch_opened_img"] = resource_filename(
            "brainrender.gui.icons", f"down_{self.theme}.svg"
        )
        self.palette["checked_img"] = resource_filename(
            "brainrender.gui.icons", f"checkedbox_{self.theme}.svg"
        )
        self.palette["unchecked_img"] = resource_filename(
            "brainrender.gui.icons", f"box_{self.theme}.svg"
        )

    def make_left_navbar(self):
        """
        Creates the structures tree hierarchy widget and populates
        it with structures names from the brainglobe-api's Atlas.hierarchy
        tree view.
        """
        # Create QTree widget
        treeView = QTreeView()
        treeView.setExpandsOnDoubleClick(False)
        treeView.setHeaderHidden(True)
        treeView.setStyleSheet(update_css(tree_css, self.palette))
        treeView.setWordWrap(False)

        treeModel = QStandardItemModel()
        rootNode = treeModel.invisibleRootItem()

        # Add element's hierarchy
        tree = self.scene.atlas.hierarchy
        items = {}
        for n, node in enumerate(tree.expand_tree()):
            # Get Node info
            node = tree.get_node(node)
            if node.tag in ["VS", "fiber tracts"]:
                continue

            # Get brainregion name
            name = self.scene.atlas._get_from_structure(
                node.identifier, "name"
            )

            # Create Item
            item = StandardItem(
                name,
                node.tag,
                tree.depth(node.identifier),
                self.palette["text"],
            )

            # Get/assign parents
            parent = tree.parent(node.identifier)
            if parent is not None:
                if parent.identifier not in items.keys():
                    continue
                else:
                    items[parent.identifier].appendRow(item)

            # Keep track of added nodes
            items[node.identifier] = item
            if n == 0:
                root = item

        # Finish up
        rootNode.appendRow(root)
        treeView.setModel(treeModel)
        treeView.expandToDepth(2)
        self.treeView = treeView

        return treeView

    def make_right_navbar(self):
        """
        Creates the widgets in the right navbar.
        """
        # make layout
        layout = QVBoxLayout()

        # Add label
        layout.addWidget(QLabel("Add actors"))

        # Add buttons
        for bname in self.right_navbar_button_names:
            btn = QPushButton(bname.capitalize(), self)
            btn.setObjectName(bname.replace(" ", "_"))
            self.buttons[bname.replace(" ", "_")] = btn
            layout.addWidget(btn)

        # Add label
        lbl = QLabel("Actors")
        lbl.setObjectName("LabelWithBorder")
        layout.addWidget(lbl)

        # add list widget
        self.actors_list = QListWidget()
        self.actors_list.setObjectName("actors_list")
        layout.addWidget(self.actors_list)

        # Add label
        lbl = QLabel("Actor properties")
        lbl.setObjectName("LabelWithBorder")
        layout.addWidget(lbl)

        # Actor Alpha
        alphalabel = QLabel("Alpha")
        alphalabel.setObjectName("PropertyName")
        self.alpha_textbox = QLineEdit(self)
        self.alpha_textbox.setObjectName("Property")
        layout.addWidget(alphalabel)
        layout.addWidget(self.alpha_textbox)

        # Actor Color
        colorlabel = QLabel("Color")
        colorlabel.setObjectName("PropertyName")
        self.color_textbox = QLineEdit(self)
        self.color_textbox.setObjectName("Property")
        layout.addWidget(colorlabel)
        layout.addWidget(self.color_textbox)

        # Add label
        lbl = QLabel("Show structures tree")
        lbl.setObjectName("LabelWithBorder")
        layout.addWidget(lbl)

        btn = QPushButton("Show structures tree", self)
        self.buttons[btn.text().lower().replace(" ", "_")] = btn
        layout.addWidget(btn)

        # set spacing
        layout.addStretch(5)
        layout.setSpacing(20)

        # make widget
        widget = QWidget()
        widget.setObjectName("RightNavbar")
        widget.setLayout(layout)

        return widget

    def make_central_column(self):
        """
        Creates vtkWidget for the vedo plotter and a few
        useful buttons, for the central part of the GUI
        """
        # Create layout, add canvas and buttons
        layout = QVBoxLayout()
        layout.addWidget(self.vtkWidget)

        # Make buttons
        boxes = [QHBoxLayout(), QHBoxLayout()]
        for n, bname in enumerate(self.central_column_button_names):
            btn = QPushButton(bname.capitalize(), self)
            btn.setObjectName(bname.replace(" ", "_"))
            self.buttons[bname.replace(" ", "_")] = btn

            if n == 0:
                boxes[0].addWidget(btn)
            else:
                boxes[1].addWidget(btn)

        hlayout = QHBoxLayout()

        widget = QWidget()
        widget.setLayout(boxes[0])
        widget.setObjectName("ScreenshotButtonLayout")
        hlayout.addWidget(widget)

        widget = QWidget()
        widget.setLayout(boxes[1])
        hlayout.addWidget(widget)

        widget = QWidget()
        widget.setObjectName("CentralColumn_buttons")
        widget.setLayout(hlayout)

        layout.addWidget(widget)

        # make widget
        widget = QWidget()
        widget.setObjectName("CentralColumn")
        widget.setLayout(layout)

        return widget

    def initUI(self):
        """
        Define UI elements of the app's main window
        """
        # Create navbars
        self.treeView = self.make_left_navbar()

        # Make overall layout
        main_layout = QHBoxLayout()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.treeView)
        splitter.addWidget(self.make_central_column())
        splitter.addWidget(self.make_right_navbar())

        splitter.setSizes([200, 700, 10])
        main_layout.addWidget(splitter)

        self.treeView.setHidden(True)

        # Create main window widget
        main_widget = QWidget()
        main_widget.setObjectName("MainWidget")
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
