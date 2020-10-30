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
    if output is None:
        screenshot_kwargs = {}
    else:
        screenshot_kwargs = dict(folder=output)

    app = QApplication(sys.argv)
    app.setApplicationName("Brainrender GUIs")
    ex = App(atlas=atlas, axes=axes, screenshot_kwargs=screenshot_kwargs)
    app.aboutToQuit.connect(ex.onClose)
    ex.show()
    sys.exit(app.exec_())
