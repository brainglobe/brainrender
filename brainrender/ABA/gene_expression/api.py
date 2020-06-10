import numpy as np
from vtkplotter import Volume

import brainrender

# from brainrender.ABA.gene_expression.ge_utils import read_raw
from brainrender.Utils.paths_manager import Paths

# from brainrender.Utils.webqueries import request


class GeneExpressionAPI(Paths):
    voxel_size = 200  # um
    grid_size = [58, 41, 67]  # number of voxels along each direction

    all_genes_url = (
        "http://api.brain-map.org/api/v2/data/query.json?criteria="
        + "model::Gene,"
        + "rma::criteria,products[abbreviation$eq'DevMouse'],"
        + "rma::options,[tabular$eq'genes.id','genes.acronym+as+gene_symbol','genes.name+as+gene_name',"
        + "'genes.entrez_id+as+entrez_gene_id','genes.homologene_id+as+homologene_group_id'],"
        + "[order$eq'genes.acronym']"
        + "&num_rows=all&start_row=0"
    )

    def __init__(self, base_dir=None, **kwargs):
        super().__init__(base_dir, **kwargs)

        # Get metadata about all available genes
        self.genes = None  # when necessary gene data can be downloaded with self.get_all_genes

        # TODO make methods to download and cache data

    # TODO make decorator to catch this is no internet connection
    def get_all_genes(self):
        """
            Download metadata about all the genes available in the Allen gene expression dataset
        """
        # res = request(url)
        # return pd.DataFrame(res.json()["msg"])
        return

    def get_gene_data(self, gene):
        # TODO: check if gene cached, if yes load
        # TODO if not load, but fail on no internet
        # TODO after loading cache the results
        if not isinstance(gene, list):
            gene = [gene]

    def griddata_to_volume(
        self, griddata, min_quantile=None, min_value=None, **kwargs
    ):
        """
            Takes a 3d numpy array with volumetric gene expression
            and returns a vtkplotter.Volume.isosurface actor.
            The isosurface needs a lower bound threshold, this can be
            either a user defined hard value (min_value) or the value
            corresponding to some percentile of the gene expression data.

            :param griddata: np.ndarray, 3d array with gene expression data
            :param min_quantile: float, percentile for threshold
            :param min_value: float, value for threshold
        """
        # Check inputs
        if not isinstance(griddata, np.ndarray):
            raise ValueError("Griddata should be a numpy array")
        if not len(griddata.shape) == 3:
            raise ValueError("Griddata should be a 3d array")

        # Get threshold
        if min_quantile is None and min_value is None:
            th = 0
        elif min_value is not None:
            if not isinstance(min_quantile, (int, float)):
                raise ValueError("min_values should be a float")
            th = min_value
        else:
            if not isinstance(min_quantile, (float, int)):
                raise ValueError(
                    "min_values should be a float in range [0, 1]"
                )
            if 0 > min_quantile or 1 < min_quantile:
                raise ValueError(
                    "min_values should be a float in range [0, 1]"
                )
            # TODO
            raise NotImplementedError("Need to make this happend")

        # Create mesh
        color = kwargs.pop("color", brainrender.DEFAULT_STRUCTURE_COLOR)
        actor = Volume(
            griddata,
            spacing=[self.voxel_size, self.voxel_size, self.grid_size],
        )
        actor = actor.isosurface(vmin=th).c(color)
        return actor
