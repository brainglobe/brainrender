import sys

sys.path.append("./")

from brainrender.apps import heatmap


"""
    This example shows how to use brainrender to show a 'heatmap' visualization
    in which brain regions are assigned different colors based on  a dictionary
    mapping scalar values to a set of brainregions
"""

values = dict(  # scalar values for each region
    TH=1,
    RSP=0.2,
    AI=0.4,
    SS=-3,
    MO=2.6,
    PVZ=-4,
    LZ=-3,
    VIS=2,
    AUD=0.3,
    RHP=-0.2,
    STR=0.5,
    CB=0.5,
    FRP=-1.7,
    HIP=3,
    PA=-4,
)


heatmap(
    values,
    position=-400,  # displacement along the AP axis relative to midpoint
    orientation="frontal",  # or 'sagittal', or 'top'
    thickness=1000,  # thickness of the slices used for rendering (in microns)
    title="frontal",
    vmin=-5,
    vmax=3,
)
