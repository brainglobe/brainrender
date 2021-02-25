from qtpy.QtWidgets import QApplication
import sys
import click

from brainrender.gui.app import App


def launch(*args, atlas_name=None, output=None, screenshots_folder=None):
    """
    Launches the application
    """
    if output is None:
        screenshot_kwargs = output
    else:
        screenshot_kwargs = screenshots_folder

    app = QApplication(sys.argv)
    app.setApplicationName("Brainrender GUIs")
    ex = App(
        *args, atlas_name=atlas_name, screenshots_folder=screenshots_folder
    )
    app.aboutToQuit.connect(ex.onClose)
    ex.show()
    sys.exit(app.exec_())


@click.command()
@click.option("-x", "--axes", is_flag=True, default=False)
@click.option("-a", "--atlas", default=None)
@click.option("-o", "--output", default=None)
def clilaunch(atlas=None, axes=False, output=None):
    app = QApplication(sys.argv)
    app.setApplicationName("Brainrender GUIs")
    ex = App(atlas_name=atlas, axes=axes, screenshots_folder=output)
    app.aboutToQuit.connect(ex.onClose)
    ex.show()
    sys.exit(app.exec_())
