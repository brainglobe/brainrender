from qtpy.QtWidgets import QFileDialog
from pathlib import Path
import numpy as np
from loguru import logger

from brainrender.gui.widgets.add_from_file import AddFromFileWindow
from brainrender.gui.utils import (
    get_color_from_string,
    get_alpha_from_string,
)
from brainrender.actors import Points


class AddFromFile:
    def __init__(self):
        """
        Collection of functions to load data from files
        and add it to the GUI's brainrender Scene.
        """
        return

    def __add_from_file(self, fun, name_from_file=True):
        """
        General function for selecting, loading
        and adding to scene a file.

        Arguments:
        -----------

        fun: function. One of Scene's methods used to add the file's
                content to the scene.
        name_from_file: bool, optional. If True the actor's name is the name of the files loaded
        """
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog

        fname, _ = QFileDialog.getOpenFileName(
            self,
            "QFileDialog.getOpenFileName()",
            "",
            "All Files (*)",
            options=options,
        )

        if not fname:
            return
        else:
            # Get actor color and alpha
            dialog = AddFromFileWindow(self, self.palette)
            dialog.exec()

            alpha = get_alpha_from_string(dialog.alpha_textbox.text())
            color = get_color_from_string(dialog.color_textbox.text())

            # Add actor
            act = fun(fname)
            if not isinstance(act, (tuple, list)):
                act = [act]

            # Edit actor
            for actor in act:
                actor.name = Path(fname).name

                if color != "default":
                    actor.mesh.c(color)

                if alpha is not None:
                    actor.mesh.alpha(alpha)

            # Update
            self._update()

    def add_from_file_object(self):
        """
        Add to scene from brainrender.stl, .obj and .vtk files.
        Method of the corresponding button
        """
        logger.debug("GUI: adding mesh (e.g. obj) form file")
        self.__add_from_file(self.scene.add)

    def _get_cells_mesh(self, fp):
        data = np.load(fp)
        return self.scene.add(Points(data))

    def add_from_file_cells(self):
        """
        Add to scene from brainrender.npy files with cell coordinates data.
        Method of the corresponding button
        """
        logger.debug("GUI: adding CELLS from file")
        self.__add_from_file(self._get_cells_mesh)
