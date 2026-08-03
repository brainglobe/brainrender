"""Create actors for rendering axonal projection streamlines."""

from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger
from vedo import Mesh, merge
from vedo.shapes import Spheres, Tube

from brainrender.actor import Actor


def make_streamlines(
    *streamlines: pd.DataFrame,
    color: str = "salmon",
    alpha: float = 1,
    radius: float = 10,
    show_injection: bool = True,
) -> list["Streamlines"]:
    """
    Create Streamlines actors from one or more dataframes.

    Parameters
    ----------
    *streamlines
        DataFrames with streamlines data.
    color
        Colour name. Default ``"salmon"``.
    alpha
        Transparency. Default 1.
    radius
        Radius of the Tube mesh. Default 10.
    show_injection
        If True, spheres mark the injection sites. Default True.

    Returns
    -------
    list of Streamlines
        A list of Streamlines actors, one for each input DataFrame.
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
    Actor created from streamlines projection data.

    Renders axonal streamlines as tube meshes, optionally marking
    injection sites with spheres.
    """

    def __init__(
        self,
        data: pd.DataFrame | str | Path,
        radius: float = 10,
        color: str = "salmon",
        alpha: float = 1,
        show_injection: bool = True,
        name: str | None = None,
    ) -> None:
        """
        Parameters
        ----------
        data
            DataFrame with streamlines points data, or a path to a JSON file.
        radius
            Radius of the Tube mesh. Default 10.
        color
            Colour name. Default ``"salmon"``.
        alpha
            Transparency. Default 1.
        show_injection
            If True, spheres mark the injection sites. Default True.
        name
            Actor name. Default ``"Streamlines"``.

        Raises
        ------
        TypeError
            If ``data`` is not a DataFrame or a path to a JSON file.
        """
        logger.debug("Creating a streamlines actor")
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

    def _make_mesh(
        self,
        data: pd.DataFrame,
        show_injection: bool = True,
    ) -> Mesh:
        """
        Build a merged vedo mesh from streamlines and injection sites.

        Parameters
        ----------
        data
            DataFrame with ``lines`` and ``injection_sites`` columns.
        show_injection
            If True, add spheres at injection sites.

        Returns
        -------
        vedo.Mesh
            A merged vedo mesh containing the streamlines and, optionally, injection sites.
        """
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
