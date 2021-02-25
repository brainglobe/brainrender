from qtpy.QtGui import QFont, QColor, QStandardItem


class StandardItem(QStandardItem):
    def __init__(self, txt="", tag=None, depth=0, color=None):
        """
        Items in the tree list with some
        extended functionality to specify/update
        their look.
        """
        super().__init__()
        self.depth = depth  # depth in the hierarchy structure
        self.tag = tag

        self._checked = False

        # Set font color/size
        self.toggle_active()

        # Set text
        self.setEditable(False)
        rgb = color.replace(")", "").replace(" ", "").split("(")[-1].split(",")
        self.setForeground(QColor(*[int(r) for r in rgb]))
        self.setText(txt)

        # Set checkbox
        # self.setFlags(
        #     self.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable
        # )
        # self.setCheckState(Qt.Unchecked)

    def toggle_active(self):
        """
        When a mesh corresponding to the item's region
        get's rendered, change the font to bold
        to highlight the fact.
        """
        fnt = QFont("Roboto", 14)
        if self._checked:
            fnt.setBold(True)
        else:
            fnt.setBold(False)
        self.setFont(fnt)
