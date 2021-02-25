import pandas as pd
import os
import sys
from loguru import logger


from brainrender.atlas_specific.allen_brain_atlas.gene_expression.ge_utils import (
    check_gene_cached,
    load_cached_gene,
    download_and_cache,
)

from brainrender import base_dir
from brainrender._io import request, fail_on_no_connection
from brainrender.actors import Volume


class GeneExpressionAPI:
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

    gene_experiments_url = (
        "http://api.brain-map.org/api/v2/data/query.json?criteria=model::SectionDataSet,"
        + "rma::criteria,[failed$eq'false'],products[abbreviation$eq'Mouse'],genes[acronym$eq'-GENE_SYMBOL-']"
    )

    download_url = "http://api.brain-map.org/grid_data/download/EXP_ID?include=energy,intensity,density"

    gene_expression_cache = base_dir / "GeneExpressionCache"
    gene_name = None

    def __init__(self):
        # Get metadata about all available genes
        self.genes = None  # when necessary gene data can be downloaded with self.get_all_genes
        self.gene_expression_cache.mkdir(exist_ok=True)

    @fail_on_no_connection
    def get_all_genes(self):
        """
        Download metadata about all the genes available in the Allen gene expression dataset
        """
        res = request(self.all_genes_url)
        return pd.DataFrame(res.json()["msg"])

    def get_gene_id_by_name(self, gene_name):
        self.gene_name = self.gene_name or gene_name
        if self.genes is None:
            self.genes = self.get_all_genes()

        if gene_name not in self.genes.gene_symbol.values:
            print(
                f"Gene name {gene_name} doesnt appear in the genes dataset, nothing to return\n"
                + "You can search for you gene here: https://mouse.brain-map.org/"
            )
            return None
        else:
            return int(
                self.genes.loc[self.genes.gene_symbol == gene_name].id.values[
                    0
                ]
            )

    def get_gene_symbol_by_id(self, gene_id):
        if self.genes is None:
            self.genes = self.get_all_genes()

        return self.genes.loc[
            self.genes.id == str(gene_id)
        ].gene_symbol.values[0]

    @fail_on_no_connection
    def get_gene_experiments(self, gene):
        """
        Given a gene_symbol it returns the list of ISH
        experiments for this gene

        :param gene_symbol: str
        """
        url = self.gene_experiments_url.replace("-GENE_SYMBOL-", gene)
        data = request(url).json()["msg"]

        if not len(data):
            print(f"No experiment found for gene {gene}")
            return None
        else:
            return [d["id"] for d in data]

    @fail_on_no_connection
    def download_gene_data(self, gene):
        """
        Downloads a gene's data from the Allen Institute
        Gene Expression dataset and saves to cache.
        See: http://help.brain-map.org/display/api/Downloading+3-D+Expression+Grid+Data

        :param gene: int, the gene_id for the gene being downloaded.
        """
        # Get the gene's experiment id
        exp_ids = self.get_gene_experiments(gene)

        if exp_ids is None:
            return

        # download experiment data
        for eid in exp_ids:
            print(f"Downloading data for {gene} - experiment: {eid}")
            url = self.download_url.replace("EXP_ID", str(eid))
            download_and_cache(
                url, os.path.join(self.gene_expression_cache, f"{gene}-{eid}")
            )

    def get_gene_data(self, gene, exp_id, use_cache=True, metric="energy"):
        """
        Given a list of gene ids
        """
        logger.debug(f"Getting gene data for gene: {gene} experiment {exp_id}")
        self.gene_name = self.gene_name or gene

        # Check if gene-experiment cached
        if use_cache:
            cache = check_gene_cached(self.gene_expression_cache, gene, exp_id)
        else:
            cache = False

        if not cache:  # then download it
            self.download_gene_data(gene)
            cache = check_gene_cached(self.gene_expression_cache, gene, exp_id)
            if not cache:
                raise ValueError(  # pragma: no cover
                    "Something went wrong and data were not cached"
                )

        # Load from cache
        data = load_cached_gene(cache, metric, self.grid_size)

        if sys.platform == "darwin":
            data = data.T

        return data

    def griddata_to_volume(
        self,
        griddata,
        min_quantile=None,
        min_value=None,
        cmap="bwr",
    ):
        """
        Takes a 3d numpy array with volumetric gene expression
        and returns a vedo.Volume.isosurface actor.
        The isosurface needs a lower bound threshold, this can be
        either a user defined hard value (min_value) or the value
        corresponding to some percentile of the gene expression data.

        :param griddata: np.ndarray, 3d array with gene expression data
        :param min_quantile: float, percentile for threshold
        :param min_value: float, value for threshold
        """
        return Volume(
            griddata,
            min_quantile=min_quantile,
            voxel_size=self.voxel_size,
            min_value=min_value,
            cmap=cmap,
            name=self.gene_name,
            br_class="Gene Data",
        )
