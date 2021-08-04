import pandas as pd
from vedo.shapes import Tube, Spheres
from vedo import merge
from loguru import logger
import numpy as np
from pathlib import Path


from brainrender.actor import Actor


def make_streamlines(
    *streamlines, color="salmon", alpha=1, radius=10, show_injection=True
):
    """
    Creates instances of Streamlines from data.
    :param streamlines: pd.dataframes with streamlines data
    :param radius: float. Radius of the Tube mesh used to render streamlines
    :param color: str, name of the color to be used
    :param alpha: float, transparancy
    :param show_injection: bool. If true spheres mark the injection sites
    """
    return [
        Streamlines(
            s,
            color=color,
            alpha=alpha,
            radius=radius,
            show_injection=show_injection,
        )
        for s in streamlines
    ]


class Streamlines(Actor):
    """
    Streamliens actor class.
    Creates an actor from streamlines data (from a json file parsed with: get_streamlines_data)
    """

    def __init__(
        self,
        data,
        radius=10,
        color="salmon",
        alpha=1,
        show_injection=True,
        name=None,
    ):
        """
        Turns streamlines data to a mesh.
        :param data: pd.DataFrame with streamlines points data
        :param radius: float. Radius of the Tube mesh used to render streamlines
        :param color: str, name of the color to be used
        :param alpha: float, transparancy
        :param name: str, name of the actor.
        :param show_injection: bool. If true spheres mark the injection sites
        """
        logger.debug(f"Creating a streamlines actor")
        if isinstance(data, (str, Path)):
            data = pd.read_json(data)
        elif not isinstance(data, pd.DataFrame):
            raise TypeError("Input data should be a dataframe")

        self.radius = radius
        mesh = (
            self._make_mesh(data, show_injection=show_injection)
            .c(color)
            .alpha(alpha)
            .clean()
        )

        name = name or "Streamlines"
        Actor.__init__(self, mesh, name=name, br_class="Streamliness")

    def _make_mesh(self, data, show_injection=True):
        lines = []
        if len(data["lines"]) == 1:
            try:
                lines_data = data["lines"][0]
            except KeyError:  # pragma: no cover
                lines_data = data["lines"]["0"]  # pragma: no cover
        else:
            lines_data = data["lines"]

        for line in lines_data:
            points = [[lin["x"], lin["y"], lin["z"]] for lin in line]
            lines.append(
                Tube(
                    points,
                    r=self.radius,
                    res=8,
                )
            )

        if show_injection:
            coords = np.vstack(
                [
                    list(point.values())
                    for point in data.injection_sites.iloc[0]
                ]
            )
            lines.append(
                Spheres(
                    coords,
                    r=self.radius * 10,
                    res=8,
                )
            )

        return merge(*lines)
