import click
from brainrender.scene import Scene
import brainrender


@click.command()
@click.option("-a", "--atlas", default=None, help="atlas name")
@click.option("-c", "--cartoon", is_flag=True, help="cartoon look")
@click.option("-d", "--debug", is_flag=True)
@click.option("-f", "--file", help="path to .obj or .h5 file")
@click.argument("regions", nargs=-1)
def main(regions, atlas=None, cartoon=False, debug=False, file=None):
    # Set look
    if cartoon:
        brainrender.SHADER_STYLE = "cartoon"

    # Create scene
    scene = Scene(atlas=atlas)

    # Add brain regions
    if regions is not None and len(regions) > 0:
        acts = scene.add_brain_regions(list(regions))

        # Add silhouettes
        if cartoon:
            if isinstance(acts, list):
                scene.add_silhouette(*acts)
            else:
                scene.add_silhouette(acts)

    # Add data from file
    if file is not None:
        if file.endswith(".h5"):
            scene.add_cells_from_file(file)
        else:
            try:
                scene.add_from_file(file)
            except Exception as e:
                raise ValueError(
                    f"Failed to load data from file onto scene: {file}\n{e}"
                )

    # If debug set interactive = Off and close scene
    if not debug:
        interactive = True
    else:
        interactive = False

    # Render and close
    scene.render(interactive=interactive)

    if debug:
        scene.close()
