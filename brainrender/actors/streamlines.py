import pandas as pd
from vedo.shapes import Tube
from vedo import merge

from ..actor import Actor
from ._streamlines import experiments_source_search, get_streamlines_data


def get_streamlines_for_region(region, force_download=False):
    """
        Using the Allen Mouse Connectivity data and corresponding API, this function finds expeirments whose injections
        were targeted to the region of interest and downloads the corresponding streamlines data. By default, experiements
        are selected for only WT mice and onl when the region was the primary injection target.

        :param region: str with region to use for research

    """
    # Get experiments whose injections were targeted to the region
    region_experiments = experiments_source_search(region)

    return get_streamlines_data(
        region_experiments.id.values, force_download=force_download
    )


def make_streamlines(*streamlines):
    return [Streamlines(s) for s in streamlines]


class Streamlines(Actor):
    def __init__(self, data, radius=10, color="salmon", alpha=1, name=None):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Input data should be a dataframe")

        self.radius = radius
        mesh = self._make_mesh(data).c(color).alpha(alpha)

        name = name or "Streamlines"
        Actor.__init__(self, mesh, name=name, br_class="Streamliness")

    def _make_mesh(self, data):
        lines = []
        if len(data["lines"]) == 1:
            try:
                lines_data = data["lines"][0]
            except KeyError:
                lines_data = data["lines"]["0"]
        else:
            lines_data = data["lines"]
        for line in lines_data:
            points = [[l["x"], l["y"], l["z"]] for l in line]
            lines.append(Tube(points, r=self.radius, res=8,))

        return merge(*lines)
