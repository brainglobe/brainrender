from brainatlas_api.bg_atlas import FishAtlas

from brainrender.atlases.brainglobe import BrainGlobeAtlas


class BGFishAtlas(BrainGlobeAtlas, FishAtlas):
    atlas_name = "fishatlas"

    def __init__(self, base_dir=None, **kwargs):
        BrainGlobeAtlas.__init__(self, base_dir=base_dir, **kwargs)
        FishAtlas.__init__(self)

        self.meshes_folder = self.root_dir / "meshes"
