from pathlib import Path
import pandas as pd
import numpy as np

from rich.progress import track
from vedo import shapes, merge, Cylinder

import brainrender
from brainrender.Utils.data_io import (
    load_json,
    get_probe_points_from_sharptrack,
)
from brainrender.Utils.data_manipulation import is_any_item_in_list
from brainrender.Utils.webqueries import request
from brainrender.colors import check_colors

""" 
    Code to support atlases.mouse.ABA
"""


# ---------------------------------------------------------------------------- #
#                                 TRACTOGRAPHY                                 #
# ---------------------------------------------------------------------------- #
def parse_tractography_colors(
    tractography,
    include_all_inj_regions,
    color=None,
    color_by="manual",
    VIP_regions=[],
    VIP_color=None,
    others_color="salmon",
):
    """
        parses color arguments to render tracrography data

        :param tractography: list of dictionaries with tractography data
        :param color: color of rendered tractography data
        :param color_by: str, specifies which criteria to use to color the tractography (Default value = "manual")
            Options:
                - manual: the user needs to provide a color or list of colors
                - target_region: tracts are colored according to the region where the injection was done.
                        if VIP_regions is passed, then only tracts for the VIP regions are colored

        :param VIP_regions: list of brain regions with VIP treatement (Default value = [])
        :param VIP_color: str, color to use for VIP data (Default value = None)
        :param include_all_inj_regions: bool (Default value = False)
        :param others_color: str, color for not VIP data (Default value = "white")
    """
    # check coloring mode used and prepare a list COLORS to use for coloring stuff
    if color_by == "manual":
        # check color argument
        if color is None:
            color = brainrender.TRACT_DEFAULT_COLOR
            COLORS = [color for i in range(len(tractography))]
        elif isinstance(color, list):
            if not len(color) == len(tractography):
                raise ValueError(
                    "If a list of colors is passed, it must have the same number of items as the number of tractography traces"
                )
            else:
                for col in color:
                    if not check_colors(col):
                        raise ValueError(
                            "Color variable passed to tractography is invalid: {}".format(
                                col
                            )
                        )

                COLORS = color
        else:
            if not check_colors(color):
                raise ValueError(
                    "Color variable passed to tractography is invalid: {}".format(
                        color
                    )
                )
            else:
                COLORS = [color for i in range(len(tractography))]

    elif color_by == "target_region":
        if VIP_color is not None:
            if not check_colors(VIP_color) or not check_colors(others_color):
                raise ValueError("Invalid VIP or other color passed")
            try:
                if include_all_inj_regions:
                    COLORS = [
                        VIP_color
                        if is_any_item_in_list(
                            [
                                x["abbreviation"]
                                for x in t["injection-structures"]
                            ],
                            VIP_regions,
                        )
                        else others_color
                        for t in tractography
                    ]
                else:
                    COLORS = [
                        VIP_color
                        if t["structure-abbrev"] in VIP_regions
                        else others_color
                        for t in tractography
                    ]
            except:
                raise ValueError(
                    "Something went wrong while getting colors for tractography"
                )
        else:
            COLORS = [None for t in tractography]  # will be filled up later

    else:
        raise ValueError(
            "Unrecognised 'color_by' argument {}".format(color_by)
        )

    return COLORS


def experiments_source_search(mca, SOI, *args, source=True, **kwargs):
    """
        Returns data about experiments whose injection was in the SOI, structure of interest
        :param SOI: str, structure of interest. Acronym of structure to use as seed for teh search
        :param *args: 
        :param source:  (Default value = True)
        :param **kwargs: 
        """
    """
            list of possible kwargs
                injection_structures : list of integers or strings
                    Integer Structure.id or String Structure.acronym.
                target_domain : list of integers or strings, optional
                    Integer Structure.id or String Structure.acronym.
                injection_hemisphere : string, optional
                    'right' or 'left', Defaults to both hemispheres.
                target_hemisphere : string, optional
                    'right' or 'left', Defaults to both hemispheres.
                transgenic_lines : list of integers or strings, optional
                    Integer TransgenicLine.id or String TransgenicLine.name. Specify ID 0 to exclude all TransgenicLines.
                injection_domain : list of integers or strings, optional
                    Integer Structure.id or String Structure.acronym.
                primary_structure_only : boolean, optional
                product_ids : list of integers, optional
                    Integer Product.id
                start_row : integer, optional
                    For paging purposes. Defaults to 0.
                num_rows : integer, optional
                    For paging purposes. Defaults to 2000.
        """
    transgenic_id = kwargs.pop(
        "transgenic_id", 0
    )  # id = 0 means use only wild type
    primary_structure_only = kwargs.pop("primary_structure_only", True)

    if not isinstance(SOI, list):
        SOI = [SOI]

    if source:
        injection_structures = SOI
        target_domain = None
    else:
        injection_structures = None
        target_domain = SOI

    return pd.DataFrame(
        mca.experiment_source_search(
            injection_structures=injection_structures,
            target_domain=target_domain,
            transgenic_lines=transgenic_id,
            primary_structure_only=primary_structure_only,
        )
    )


# ---------------------------------------------------------------------------- #
#                                  STREAMLINES                                 #
# ---------------------------------------------------------------------------- #
def parse_streamline(
    *args,
    filepath=None,
    data=None,
    show_injection_site=True,
    color="ivory",
    alpha=0.8,
    radius=10,
    **kwargs,
):
    """
        Given a path to a .json file with streamline data (or the data themselves), render the streamline as tubes actors.
        Either  filepath or data should be passed

        :param filepath: str, optional. Path to .json file with streamline data (Default value = None)
        :param data: panadas.DataFrame, optional. DataFrame with streamline data. (Default value = None)
        :param color: str color of the streamlines (Default value = 'ivory')
        :param alpha: float transparency of the streamlines (Default value = .8)
        :param radius: int radius of the streamlines actor (Default value = 10)
        :param show_injection_site: bool, if True spheres are used to render the injection volume (Default value = True)
        :param *args: 
        :param **kwargs: 

    """
    if filepath is not None and data is None:
        data = load_json(filepath)
    elif filepath is None and data is not None:
        pass
    else:
        raise ValueError(
            "Need to pass eiteher a filepath or data argument to parse_streamline"
        )

    # create actors for streamlines
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
        lines.append(
            shapes.Tube(
                points,
                r=radius,
                c=color,
                alpha=alpha,
                res=brainrender.STREAMLINES_RESOLUTION,
            )
        )

    coords = []
    if show_injection_site:
        if len(data["injection_sites"]) == 1:
            try:
                injection_data = data["injection_sites"][0]
            except KeyError:
                injection_data = data["injection_sites"]["0"]
        else:
            injection_data = data["injection_sites"]

        for inj in injection_data:
            coords.append(list(inj.values()))
        spheres = [shapes.Spheres(coords, r=brainrender.INJECTION_VOLUME_SIZE)]
    else:
        spheres = []

    merged = merge(*lines, *spheres)
    merged.color(color)
    merged.alpha(alpha)
    return [merged]


def make_url_given_id(expid):
    """
        Get url of JSON file for an experiment, give it's ID number

        :param expid: int with experiment ID number

    """
    return "https://neuroinformatics.nl/HBP/allen-connectivity-viewer/json/streamlines_{}.json.gz".format(
        expid
    )


def download_streamlines(eids, streamlines_folder=None):  # pragma: no cover
    """
        Given a list of expeirmental IDs, it downloads the streamline data from the https://neuroinformatics.nl cache and saves them as
        json files. 

        :param eids: list of integers with experiments IDs
        :param streamlines_folder: str path to the folder where the JSON files should be saved, if None the default is used (Default value = None)

    """
    streamlines_folder = Path(streamlines_folder)

    if not isinstance(eids, (list, np.ndarray, tuple)):
        eids = [eids]

    filepaths, data = [], []
    for eid in track(eids, total=len(eids), description="downloading"):
        url = make_url_given_id(eid)
        jsonpath = streamlines_folder / f"{eid}.json"
        filepaths.append(str(jsonpath))

        if not jsonpath.exists():
            response = request(url)

            # Write the response content as a temporary compressed file
            temp_path = streamlines_folder / "temp.gz"
            with open(str(temp_path), "wb") as temp:
                temp.write(response.content)

            # Open in pandas and delete temp
            url_data = pd.read_json(
                str(temp_path), lines=True, compression="gzip"
            )
            temp_path.unlink()

            # save json
            url_data.to_json(str(jsonpath))

            # append to lists and return
            data.append(url_data)
        else:
            data.append(pd.read_json(str(jsonpath)))
    return filepaths, data


def extract_ids_from_csv(
    csv_file, download=False, **kwargs
):  # pragma: no cover
    """
        Parse CSV file to extract experiments IDs and link to downloadable streamline data
    
        Given a CSV file with info about experiments downloaded from: http://connectivity.brain-map.org
        extract experiments ID and get links to download (compressed) streamline data from https://neuroinformatics.nl.
        Also return the experiments IDs to download data from: https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html
        

        :param csv_file: str with path to csv file
        :param download: if True the data are downloaded automatically (Default value = False)
        :param **kwargs: 

    """
    data = pd.read_csv(csv_file)

    if not download:
        print("To download compressed data, click on the following URLs:")
        for eid in data.id.values:
            url = make_url_given_id(eid)
            print(url)

        print("\n")
        string = ""
        for x in data.id.values:
            string += "{},".format(x)

        print(
            "To download JSON directly, go to: https://neuroinformatics.nl/HBP/allen-connectivity-viewer/streamline-downloader.html"
        )
        print(
            "and  copy and paste the following experiments ID in the 'Enter the Allen Connectivity Experiment number:' field."
        )
        print(
            "You can copy and paste each individually or a list of IDs separated by a comma"
        )
        print("IDs: {}".format(string[:-1]))
        print("\n")

        return data.id.values
    else:
        return download_streamlines(data.id.values, **kwargs)


# ---------------------------------------------------------------------------- #
#                                  SHARPTRACK                                  #
# ---------------------------------------------------------------------------- #


def parse_sharptrack(
    atlas,
    probe_points_file,
    name,
    color_by_region=True,
    color="salmon",
    radius=30,
    probe_color="blackboard",
    probe_radius=15,
    probe_alpha=1,
):
    """
            Visualises the position of an implanted probe in the brain. 
            Uses the location of points along the probe extracted with SharpTrack
            [https://github.com/cortex-lab/allenCCF].
            It renders the position of points along the probe and a line fit through them.
            Code contributed by @tbslv on github. 
        """

    # Points params
    params = dict(color_by_region=True, color="salmon", radius=30, res=12,)

    # Get the position of probe points and render
    probe_points_df = get_probe_points_from_sharptrack(probe_points_file)

    # Fit a line through the points [adapted from SharpTrack by @tbslv]
    r0 = np.mean(probe_points_df.values, axis=0)
    coords = probe_points_df.values - r0
    U, S, V = np.linalg.svd(coords)
    direction = V.T[:, 0]

    # Find intersection with brain surface
    root_mesh = atlas._get_structure_mesh("root")
    p0 = direction * np.array([-1]) + r0
    p1 = (
        direction * np.array([-15000]) + r0
    )  # end point way outside of brain, on probe trajectory though
    pts = root_mesh.intersectWithLine(p0, p1)

    # Define top/bottom coordinates to render as a cylinder
    top_coord = pts[0]
    length = np.sqrt(np.sum((probe_points_df.values[-1] - top_coord) ** 2))
    bottom_coord = top_coord + direction * length

    # Render probe as a cylinder
    probe = Cylinder(
        [top_coord, bottom_coord],
        r=probe_radius,
        alpha=probe_alpha,
        c=probe_color,
    )
    probe.name = name

    return probe_points_df, params, probe, color
