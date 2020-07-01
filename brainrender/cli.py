import click
from brainrender.scene import Scene
import brainrender


@click.command()
@click.option("-a", "--atlas", default=None, help="atlas name")
@click.option("-c", "--cartoon", is_flag=True, help="cartoon look")
@click.option("-d", "--debug", is_flag=True)
@click.argument("regions", nargs=-1)
def main(regions, atlas=None, cartoon=False, debug=False):
    if cartoon:
        brainrender.SHADER_STYLE = "cartoon"

    scene = Scene(atlas=atlas)

    if regions is not None and len(regions) > 0:
        acts = scene.add_brain_regions(list(regions))

        if isinstance(acts, list):
            scene.add_mesh_silhouette(*acts)
        else:
            scene.add_mesh_silhouette(acts)

    if not debug:
        interactive = True
    else:
        interactive = False

    scene.render(interactive=interactive)

    if debug:
        scene.close()
