"""Atlas subclass adding region and plane Actor support for scenes."""

import numpy as np
from brainglobe_atlasapi.bg_atlas import BrainGlobeAtlas
from loguru import logger
from vedo import Plane

from brainrender import settings
from brainrender._io import load_mesh_from_file
from brainrender._utils import return_list_smart
from brainrender.actor import Actor


class Atlas(BrainGlobeAtlas):
    """
    Subclass of BrainGlobeAtlas with helpers.

    Parameters
    ----------
    atlas_name : str or None, optional
        Falls back to ``settings.DEFAULT_ATLAS`` if None.
    check_latest : bool, optional
        Check for the latest atlas version. Default True.
    """

    def __init__(self, atlas_name=None, check_latest=True):
        atlas_name = atlas_name or settings.DEFAULT_ATLAS
        self.atlas_name = atlas_name
        logger.debug(f"Generating ATLAS: {atlas_name}")

        try:
            super().__init__(atlas_name=atlas_name, print_authors=False)
        except TypeError:
            # The latest version of BGatlas has no print_authors argument
            super().__init__(atlas_name=atlas_name, check_latest=check_latest)

    @property
    def zoom(self):
        """
        Returns the best camera zoom given the atlas resolution.
        """
        res = np.max(self.metadata["resolution"])

        if self.atlas_name == "allen_human_500um":
            logger.debug(
                "ATLAS: setting zoom manually for human atlas, atlas needs fixing"
            )
            return 350
        else:
            return 40 / res

    def _get_region_color(self, region):
        """
        Gets the rgb color of a region in the atlas.

        Parameters
        ----------
        region : str or int

        Returns
        -------
        list of float
        """
        return [
            x / 255 for x in self._get_from_structure(region, "rgb_triplet")
        ]

    def get_region(self, *regions, alpha=1, color=None):
        """
        Get brain regions meshes as Actors.

        Parameters
        ----------
        *regions : str
            Region acronyms or IDs.
        alpha : float, optional
            Mesh transparency. Default 1.
        color : str or None, optional
            Uses atlas RGB colour if None.

        Returns
        -------
        Actor or list of Actor or None
        """
        if not regions:
            return None

        _color = color
        actors = []
        for region in regions:
            if (
                region not in self.lookup_df.acronym.values
                and region not in self.lookup_df["id"].values
            ):
                print(
                    f"The region {region} doesn't seem to belong to the atlas being used: {self.atlas_name}. Skipping"
                )
                continue

            # Get mesh
            obj_file = str(self.meshfile_from_structure(region))
            try:
                mesh = load_mesh_from_file(obj_file, color=color, alpha=alpha)
            except FileNotFoundError:
                print(
                    f"The region {region} is in the onthology but does not have a corresponding volume in the atlas being used: {self.atlas_name}. Skipping"
                )
                continue

            # Get color
            color = color or self._get_region_color(region)

            # Make actor
            actor = Actor(mesh, name=region, br_class="brain region")
            actor.c(color).alpha(alpha)
            actors.append(actor)

            # reset color to input
            color = _color

        return return_list_smart(actors)

    def get_plane(
        self,
        pos=None,
        norm=None,
        plane=None,
        sx=None,
        sy=None,
        color="lightgray",
        alpha=0.25,
        **kwargs,
    ):
        """
        Returns a plane going through a point at pos, oriented
        orthogonally to the vector norm and of width and height
        sx, sy.

        Parameters
        ----------
        pos : array-like or None, optional
            (x, y, z) the plane passes through. Defaults to root centre of mass.
        norm : array-like or None, optional
            Normal vector. Derived from *plane* if not given.
        plane : str or None, optional
            ``"sagittal"``, ``"horizontal"``, or ``"frontal"``.
        sx, sy : int or None, optional
            Width and height. Inferred from root bounds if None.
        color : str, optional
            Default ``"lightgray"``.
        alpha : float, optional
            Default 0.25.

        Returns
        -------
        Actor

        Raises
        ------
        ValueError
            If *plane* has no matching normal in the atlas space.
        """
        axes_pairs = dict(sagittal=(0, 1), horizontal=(2, 0), frontal=(2, 1))

        if pos is None:
            pos = self.root._mesh.center_of_mass()

        try:
            norm = norm or self.space.plane_normals[plane]
        except KeyError:  # pragma: no cover
            raise ValueError(  # pragma: no cover
                f"Could not find normals for plane {plane}. Atlas space provides these normals: {self.space.plane_normals}"  # pragma: no cover
            )

        # Get plane width and height
        idx_pair = (
            axes_pairs[plane]
            if plane is not None
            else axes_pairs["horizontal"]
        )

        bounds = self.root.bounds()
        root_bounds = [
            [bounds[0], bounds[1]],
            [bounds[2], bounds[3]],
            [bounds[4], bounds[5]],
        ]

        wh = [float(np.diff(root_bounds[i])[0]) for i in idx_pair]
        if sx is None:
            sx = wh[0]
        if sy is None:
            sy = wh[1]

        # return plane
        return Actor(
            Plane(pos=pos, normal=norm, s=(sx, sy), c=color, alpha=alpha),
            name=f"Plane at {pos} norm: {norm}",
            br_class="plane",
        )
