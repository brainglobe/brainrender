from brainrender.atlases.brainglobe import BrainGlobeAtlasBase, BrainGlobeAtlas
from brainrender.atlases.base import Atlas
from brainrender.atlases.mouse import ABA25Um, ABA
import warnings


def generate_bgatlas_on_the_fly(atlas, atlas_name, *args, **kwargs):
    master = None

    res = atlas_name.split("_")[2]
    if "mouse" in atlas_name:
        if res == "25um":
            return ABA25Um(*args, **kwargs)

    if master is None:
        warnings.warn(
            f"No brainrender atlas class found for brainglobe atlas {atlas_name}, using BrainGlobeAtlas."
        )
        master = BrainGlobeAtlas
        sub = BrainGlobeAtlasBase

    # Create new atlas
    new_atlas = type(
        f"bgatlas_{atlas_name}", (master, sub), atlas.__dict__.copy()
    )

    new = new_atlas(atlas)
    return new
