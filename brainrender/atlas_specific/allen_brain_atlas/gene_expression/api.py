"""API client for downloading Allen Brain Atlas gene expression data."""

import os
import sys
from time import sleep

import numpy.typing as npt
import pandas as pd
import requests
from loguru import logger

from brainrender import base_dir
from brainrender._io import fail_on_no_connection, request
from brainrender.actors import Volume
from brainrender.atlas_specific.allen_brain_atlas.gene_expression.ge_utils import (
    check_gene_cached,
    download_and_cache,
    load_cached_gene,
)


class GeneExpressionAPI:
    """Client for querying and downloading Allen Brain Atlas gene expression data."""

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
    gene_name: str | None = None

    def __init__(self) -> None:
        # Get metadata about all available genes
        self.genes: pd.DataFrame | None = (
            None  # when necessary gene data can be downloaded with self.get_all_genes
        )
        self.gene_expression_cache.mkdir(exist_ok=True)

    @fail_on_no_connection
    def get_all_genes(self) -> pd.DataFrame:
        """
        Download metadata about all genes in the Allen gene expression dataset.

        Returns
        -------
        pd.DataFrame
        """
        res = request(self.all_genes_url)
        return pd.DataFrame(res.json()["msg"])

    def get_gene_id_by_name(self, gene_name: str) -> int | None:
        """
        Return the Allen gene ID for a given gene symbol.

        Parameters
        ----------
        gene_name
            Gene symbol.

        Returns
        -------
        int or None
            Gene ID, or None if the gene is not found.
        """
        self.gene_name = self.gene_name or gene_name
        if self.genes is None:
            self.genes = self.get_all_genes()

        if gene_name not in self.genes.gene_symbol.values:
            print(
                f"Gene name {gene_name} doesn't appear in the genes dataset, nothing to return\n"
                + "You can search for you gene here: https://mouse.brain-map.org/"
            )
            return None
        else:
            return int(
                self.genes.loc[self.genes.gene_symbol == gene_name].id.values[
                    0
                ]
            )

    def get_gene_symbol_by_id(self, gene_id: int | str) -> str:
        """
        Return the gene symbol for a given Allen gene ID.

        Parameters
        ----------
        gene_id
            Allen gene ID.

        Returns
        -------
        str
        """
        if self.genes is None:
            self.genes = self.get_all_genes()

        return self.genes.loc[
            self.genes.id == str(gene_id)
        ].gene_symbol.values[0]

    @fail_on_no_connection
    def get_gene_experiments(self, gene: str) -> list[int] | None:
        """
        Return ISH experiment IDs for a given gene symbol.

        Parameters
        ----------
        gene
            Gene symbol.

        Returns
        -------
        list of int or None
            List of experiment IDs, or None if no experiments are found.
        """
        url = self.gene_experiments_url.replace("-GENE_SYMBOL-", gene)
        max_retries = 8
        delay = 4
        data = None

        for i in range(max_retries):
            try:
                data = request(url).json()["msg"]
                break
            except requests.exceptions.JSONDecodeError:
                print(f"Unable to connect to Allen API, retrying in {delay}")
                sleep(delay)
                delay *= 2

        if not len(data):
            print(f"No experiment found for gene {gene}")
            return None
        else:
            return [d["id"] for d in data]

    @fail_on_no_connection
    def download_gene_data(self, gene: str) -> None:
        """
        Download a gene's expression data from the Allen Institute and save to cache.
        See http://help.brain-map.org/display/api/Downloading+3-D+Expression+Grid+Data.

        Parameters
        ----------
        gene
            Gene symbol to download data for.
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

    def get_gene_data(
        self,
        gene: str,
        exp_id: int,
        use_cache: bool = True,
        metric: str = "energy",
    ) -> npt.NDArray | None:
        """
        Load gene expression data for a given gene and experiment.

        Parameters
        ----------
        gene
            Gene symbol.
        exp_id
            Experiment ID.
        use_cache
            If True, load from cache if available. Default True.
        metric
            Expression metric to load. Default ``"energy"``.

        Returns
        -------
        numpy.ndarray or None
            Gene expression data, or None if no data is available for the
            requested metric.

        Raises
        ------
        ValueError
            If data could not be cached after downloading.
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
        griddata: npt.NDArray,
        min_quantile: float | None = None,
        min_value: float | None = None,
        cmap: str = "bwr",
    ) -> Volume:
        """
        Convert a 3D gene expression array to a Volume actor.

        The isosurface threshold can be set as a hard value or as a
        percentile of the expression data.

        Parameters
        ----------
        griddata
            3D array with gene expression data.
        min_quantile
            Percentile threshold for isosurface extraction.
        min_value
            Hard value threshold for isosurface extraction.
        cmap
            Colormap name. Default ``"bwr"``.

        Returns
        -------
        Volume
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
