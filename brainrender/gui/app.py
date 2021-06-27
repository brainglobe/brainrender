from vedo import Plotter
from collections import namedtuple
import datetime
from loguru import logger
from qtpy.QtWidgets import QFrame
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import brainrender
from brainrender import Scene
from brainrender.camera import set_camera

from brainrender.gui.ui import UI
from brainrender.gui.apputils.camera_control import CameraControl
from brainrender.gui.apputils.add_from_file_control import AddFromFile
from brainrender.gui.apputils.regions_control import RegionsControl
from brainrender.gui.apputils.actors_control import ActorsControl

from brainrender.gui.widgets.actors_list import update_actors_list
from brainrender.gui.widgets.screenshot_modal import ScreenshotModal


class App(
    Scene, UI, CameraControl, AddFromFile, RegionsControl, ActorsControl
):
    startup = True  # some things only run once
    actors = {}  # stores actors and status
    camera_orientation = None  # used to manually set camera orientation

    def __init__(self, *args, atlas_name=None, axes=None, **kwargs):
        """
        Initialise the qtpy app and the brainrender scene.

        Arguments:
        ----------

        atlas_name: str/None. Name of the brainglobe atlas to use
        axes: bool. If true axes are shown in the brainrender render
        """
        logger.debug("Creating brainrender GUI")

        # make a vtk widget for the vedo plotter
        frame = QFrame()
        self.vtkWidget = QVTKRenderWindowInteractor(frame)

        # Get vtkWidget plotter and creates a scene embedded in it
        new_plotter = Plotter(qtWidget=self.vtkWidget)
        self.scene = Scene(
            *args, atlas_name=atlas_name, plotter=new_plotter, **kwargs
        )

        # Initialize parent classes
        UI.__init__(self, *args, **kwargs)
        CameraControl.__init__(self)
        AddFromFile.__init__(self)
        RegionsControl.__init__(self)
        ActorsControl.__init__(self)

        # Setup brainrender plotter
        self.axes = axes
        self.atuple = namedtuple("actor", "mesh, is_visible, color, alpha")

        self.setup_scene()
        self._update()
        self.scene.render()
        self.scene._get_inset()

        # Setup widgets functionality
        self.actors_list.itemDoubleClicked.connect(
            self.actor_list_double_clicked
        )
        self.actors_list.clicked.connect(self.actor_list_clicked)

        buttons_funcs = dict(
            add_brain_regions=self.open_regions_dialog,
            add_from_file=self.add_from_file_object,
            add_cells=self.add_from_file_cells,
            show_structures_tree=self.toggle_treeview,
            take_screenshot=self.take_screenshot,
            reset=self.reset_camera,
            top=self.move_camera_top,
            side1=self.move_camera_side1,
            side2=self.move_camera_side2,
            front=self.move_camera_front,
        )

        for btn, fun in buttons_funcs.items():
            self.buttons[btn].clicked.connect(fun)

        self.treeView.clicked.connect(self.add_region_from_tree)

        self.alpha_textbox.textChanged.connect(self.update_actor_properties)
        self.color_textbox.textChanged.connect(self.update_actor_properties)

        self.startup = False

    def take_screenshot(self):
        logger.debug("GUI: taking screenshot")
        self._update()
        self.scene.plotter.render()

        # Get savename
        self.scene.screenshots_folder.mkdir(exist_ok=True)

        savename = str(self.scene.screenshots_folder / "brainrender_gui")
        savename += (
            f'_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}' + ".png"
        )
        print(f"\nSaving screenshot at {savename}\n")
        self.scene.screenshot(name=savename)

        # show success message
        dialog = ScreenshotModal(self, self.palette)
        dialog.exec()

    # ------------------------------ Toggle treeview ----------------------------- #
    def toggle_treeview(self):
        """
        Method for the show structures tree button.
        It toggles the visibility of treeView widget
        and adjusts the button's text accordingly.
        """
        logger.debug("GUI: toggle tree view")
        if not self.treeView.isHidden():
            self.buttons["show_structures_tree"].setText(
                "Show structures tree"
            )
        else:
            self.buttons["show_structures_tree"].setText(
                "Hide structures tree"
            )

        self.treeView.setHidden(not self.treeView.isHidden())

    # ------------------------------- Initial setup ------------------------------ #
    def setup_scene(self):
        """
        Set scene's axes and camera
        """
        # Get axes
        if self.axes:
            self.axes = self._make_axes()
            # self.scene.add_actor(ax)
        else:
            self.axes = None

        # Fix camera
        set_camera(self.scene, self.scene.plotter.camera)

    # ---------------------------------- Update ---------------------------------- #
    def _update_actors(self):
        """
        All actors that are part of the scene are stored
        in a dictionary with key as the actor name and
        value as a 4-tuple with (Mesh, is_visible, color, alpha).
        `is_visible` is a bool that determines if the
        actor should be rendered
        """

        for actor in self.scene.actors:
            if actor is None:
                continue

            try:
                if actor.name not in self.actors.keys():
                    self.actors[actor.name] = self.atuple(
                        actor, True, actor.mesh.color(), actor.mesh.alpha()
                    )

                    if actor.silhouette is not None:
                        self.scene.plotter.remove(actor.silhouette.mesh)
                        actor.make_silhouette()

                        self.scene.plotter.add(actor.silhouette.mesh)
                        self.actors[actor.silhouette.name] = self.atuple(
                            actor.silhouette,
                            True,
                            actor.silhouette.mesh.color(),
                            actor.silhouette.mesh.alpha(),
                        )
            except AttributeError:
                # the Assembly object representing the axes should be ignore
                pass

    def _update(self):
        """
        Updates the scene's Plotter to add/remove
        meshes
        """

        # update meshes
        self.scene._apply_style()

        # Get actors to render
        self._update_actors()
        to_render = [act for act in self.actors.values() if act.is_visible]

        # Set actors look
        meshes = [act.mesh.c(act.color).alpha(act.alpha) for act in to_render]

        # Add axes
        if self.axes is not None:
            meshes.append(self.axes)

        # update actors rendered
        self.scene.plotter.show(
            *meshes,
            interactorStyle=0,
            bg=brainrender.settings.BACKGROUND_COLOR,
            resetcam=self.startup,
            zoom=None,
        )

        # Fake a button press to force canvas update
        self.scene.plotter.interactor.MiddleButtonPressEvent()
        self.scene.plotter.interactor.MiddleButtonReleaseEvent()

        # Update list widget
        update_actors_list(self.actors_list, self.actors)
        return meshes

    # ----------------------------------- Close ---------------------------------- #
    def onClose(self):
        """
        Disable the interactor before closing to prevent it from trying to act on a already deleted items
        """
        self.vtkWidget.close()
