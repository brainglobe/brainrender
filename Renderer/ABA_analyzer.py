import sys
sys.path.append('./')   # <- necessary to import packages from other directories within the project

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from collections import namedtuple
from vtkplotter import Plotter, show, interactive, Video, settings, Sphere, shapes
import warnings 

from allensdk.core.mouse_connectivity_cache import MouseConnectivityCache
from allensdk.api.queries.ontologies_api import OntologiesApi
from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi

from Utils.mouselight_parser import render_neurons
from settings import *

"""
    Useful functions
        mcc.get_experiments(cre=False,  injection_structure_ids=[])
        structure_tree.get_structures_by_acronym([])
        mca.experiment_spatial_search(seed_point=p0)
"""


class ABA:
    """[This class handles interaction with the Allen Brain Atlas datasets and APIs to get structure trees, 
    experimental metadata and results, tractography data etc. ]

    """
    volume_threshold = 0.5
    hemispheres = namedtuple("hemispheres", "left right both") # left: CONTRA, right: IPSI
    hemispheres_names = ["left", "right", "both"]
    
    # useful vars for analysis
    
    excluded_regions = ["fiber tracts"]

    # frequently used structures
    main_structures = ["PAG", "SCm", "ZI", "SCs", "GRN"]

    def __init__(self, projection_metric = "projection_energy"):
        self.projection_metric = projection_metric

        # get mouse connectivity cache and structure tree
        self.mcc = MouseConnectivityCache(manifest_file=manifest)
        self.structure_tree = self.mcc.get_structure_tree()
        
        # get ontologies API and brain structures sets
        self.oapi = OntologiesApi()
        self.get_structures_sets()

        # get reference space
        self.space = ReferenceSpaceApi()

        # mouse connectivity API [used for tractography]
        self.mca = MouseConnectivityApi()

        # Get some metadata about experiments
        self.all_experiments = self.mcc.get_experiments(dataframe=True)
        self.strains = sorted([x for x in set(self.all_experiments.strain) if x is not None])
        self.transgenic_lines = sorted(set([x for x in set(self.all_experiments.transgenic_line) if x is not None]))


    ####### GET EXPERIMENTS DATA
    def get_structures_sets(self):
        summary_structures = self.structure_tree.get_structures_by_set_id([167587189])  # main summary structures
        summary_structures = [s for s in summary_structures if s["acronym"] not in self.excluded_regions]
        self.structures = pd.DataFrame(summary_structures)

        # Other structures sets
        all_sets = pd.DataFrame(self.oapi.get_structure_sets())
        sets = ["Summary structures of the pons", "Summary structures of the thalamus", "Summary structures of the hypothalamus", "List of structures for ABA Fine Structure Search",
                    "Structures representing the major divisions of the mouse brain", "Summary structures of the midbrain", "Structures whose surfaces are represented by a precomputed mesh"]
        self.other_sets = {}
        for set_name in sets:
            set_id = all_sets.loc[all_sets.description == set_name].id.values[0]
            self.other_sets[set_name] = pd.DataFrame(self.structure_tree.get_structures_by_set_id([set_id]))

    def load_all_experiments(self, cre=False):
        """
            This function downloads all the experimental data from the MouseConnectivityCache and saves the unionized results 
            as pickled pandas dataframes. The process is slow, but the ammount of disk space necessary to save the data is small, 
            so it's worth downloading all the experiments at once to speed up subsequent analysis. 

            params:
                cre [Bool] - default (False). Set to true if you want to download experimental data from injections in cre driver lines

        """
        
        # TODO allow user to select specific cre lines?

        # Downloads all experiments from allen brain atlas and saves the results as an easy to read pkl file
        for acronym in self.structures.acronym.values:
            print("Fetching experiments for : {}".format(acronym))

            structure = self.structure_tree.get_structures_by_acronym([acronym])[0]
            experiments = self.mcc.get_experiments(cre=cre, injection_structure_ids=[structure['id']])

            print("     found {} experiments".format(len(experiments)))

            try:
                structure_unionizes = self.mcc.get_structure_unionizes([e['id'] for e in experiments], 
                                                            is_injection=False,
                                                            structure_ids=self.structures.id.values,
                                                            include_descendants=False)
            except: pass
            structure_unionizes.to_pickle(os.path.join(self.save_fld, "{}.pkl".format(acronym)))
    
    ####### ANALYSIS ON EXPERIMENTAL DATA
    def analyze_efferents(self, SOI, projection_metric = None):
        """[Loads the experiments on SOI and looks at average statistics of efferent projections]
        
        Arguments:
            SOI {[str]} -- [acronym of the structure of interest to look at]
        """
        if projection_metric is None: 
            projection_metric = self.projection_metric

        experiment_data = pd.read_pickle(os.path.join(self.save_fld, "{}.pkl".format(SOI)))
        experiment_data = experiment_data.loc[experiment_data.volume > self.volume_threshold]

        # Loop over all structures and get the injection density
        results = {"left":[], "right":[], "both":[], "id":[], "acronym":[], "name":[]}
        for target in self.structures.id.values:
            target_acronym = self.structures.loc[self.structures.id == target].acronym.values[0]
            target_name = self.structures.loc[self.structures.id == target].name.values[0]

            exp_target = experiment_data.loc[experiment_data.structure_id == target]

            exp_target_hemi = self.hemispheres(exp_target.loc[exp_target.hemisphere_id == 1], exp_target.loc[exp_target.hemisphere_id == 2], exp_target.loc[exp_target.hemisphere_id == 3])
            proj_energy = self.hemispheres(np.nanmean(exp_target_hemi.left[projection_metric].values),
                                            np.nanmean(exp_target_hemi.right[projection_metric].values),
                                            np.nanmean(exp_target_hemi.both[projection_metric].values)
            )


            for hemi in self.hemispheres_names:
                results[hemi].append(proj_energy._asdict()[hemi])
            results["id"].append(target)
            results["acronym"].append(target_acronym)
            results["name"].append(target_name)

        results = pd.DataFrame.from_dict(results).sort_values("right", na_position = "first")
        return results

    def analyze_afferents(self, SOI, projection_metric = None):
        """[Loads the experiments on SOI and looks at average statistics of afferent projections]
        
        Arguments:
            SOI {[str]} -- [structure of intereset]
        """
        if projection_metric is None: 
            projection_metric = self.projection_metric
        SOI_id = self.structure_tree.get_structures_by_acronym([SOI])[0]["id"]

        # Loop over all strctures and get projection towards SOI
        results = {"left":[], "right":[], "both":[], "id":[], "acronym":[], "name":[]}

        for origin in self.structures.id.values:
            origin_acronym = self.structures.loc[self.structures.id == origin].acronym.values[0]
            origin_name = self.structures.loc[self.structures.id == origin].name.values[0]

            experiment_data = pd.read_pickle(os.path.join(save_fld, "{}.pkl".format(origin_acronym)))
            experiment_data = experiment_data.loc[experiment_data.volume > self.volume_threshold]

            exp_target = experiment_data.loc[experiment_data.structure_id == SOI_id]
            exp_target_hemi = self.hemispheres(exp_target.loc[exp_target.hemisphere_id == 1], exp_target.loc[exp_target.hemisphere_id == 2], exp_target.loc[exp_target.hemisphere_id == 3])
            proj_energy = self.hemispheres(np.nanmean(exp_target_hemi.left[projection_metric].values),
                                            np.nanmean(exp_target_hemi.right[projection_metric].values),
                                            np.nanmean(exp_target_hemi.both[projection_metric].values)
            )
            for hemi in self.hemispheres_names:
                results[hemi].append(proj_energy._asdict()[hemi])
            results["id"].append(origin)
            results["acronym"].append(origin_acronym)
            results["name"].append(origin_name)

        results = pd.DataFrame.from_dict(results).sort_values("right", na_position = "first")
        return results

    ####### GET TRACTOGRAPHY AND SPATIAL DATA
    def get_structure_location(self, acronym):
        # ! currently this averages the location of injections in that structure, in the future it will get the centroid of the mesh corresponding to the brain region
        struct = self.structure_tree.get_structures_by_acronym([acronym])[0]
        experiments = self.mcc.get_experiments(cre=False,  injection_structure_ids=[struct["id"]])
        x, y, z  = [], [], []
        for exp in experiments:
            x.append(exp["injection_x"])
            y.append(exp["injection_y"])
            z.append(exp["injection_z"])

        return [np.nanmean(x).astype(np.int32), np.nanmean(y).astype(np.int32), np.nanmean(z).astype(np.int32)]

    def get_projection_tracts_to_target(self, acronym=None, p0=None, **kwargs):
        """[Gets tractography data for all experiments whose projections reach the brain region or location of iterest.]
        
        Keyword Arguments:
            acronym {[str]} -- [acronym of brain region of interest] (default: {None})
            p0 {[list]} -- [list of 3 floats with XYZ coordinates of point to be used as seed] (default: {None})
        
        Raises:
            ValueError: [description]
            ValueError: [description]
        
        Returns:
            [type] -- [description]
        """
        """
            mca.experiment_injection_coordinate_search also takes these arguments:
                transgenic_lines : list of integers or strings, optional
                    Integer TransgenicLine.id or String TransgenicLine.name. Specify ID 0 to exclude all TransgenicLines.
                section_data_sets : list of integers, optional
                    Ids to filter the results.
                injection_structures : list of integers or strings, optional
                    Integer Structure.id or String Structure.acronym.
                primary_structure_only : boolean, optional
                product_ids : list of integers, optional
                    Integer Product.id
        """
        # check args
        if p0 is None:
            if acronym is not None:
                p0 = self.get_structure_location(acronym)
            else: raise ValueError("Please pass either p0 or acronym")
        else:
            if acronym is not None:
                print("both p0 and acronym passed, using p0")


        # if p0 is not None and (len(p0) != 3 or not isinstance(p0[0], int)): 
        #     raise ValueError("Seed point coordinates should be an array of 3 numbers")

        tract = self.mca.experiment_spatial_search(seed_point=p0, **kwargs)

        if isinstance(tract, str): raise ValueError('Something went wrong with query')
        else:
            return tract

    def get_projection_tracts_from_target(self, acronym=None, p0=None, n_experiments=100, **kwargs):
        """[Gets tractography data for all experiments whose projections start at the brain region or location of iterest.]
            
            Keyword Arguments:
                acronym {[str]} -- [acronym of brain region of interest] (default: {None})
                p0 {[list]} -- [list of 3 floats with XYZ coordinates of point to be used as seed] (default: {None})
            
            Raises:
                ValueError: [description]
                ValueError: [description]
            
            Returns:
                [type] -- [description]
            """

        """
            mca.experiment_injection_coordinate_search also takes these arguments:
                seed_point : list of floats
                    The coordinates of a point in 3-D SectionDataSet space.
                transgenic_lines : list of integers or strings, optional
                    Integer TransgenicLine.id or String TransgenicLine.name. Specify ID 0 to exclude all TransgenicLines.
                injection_structures : list of integers or strings, optional
                    Integer Structure.id or String Structure.acronym.
                primary_structure_only : boolean, optional
        """
        # check args
        if p0 is None:
            if acronym is not None:
                p0 = self.get_structure_location(acronym)
            else: raise ValueError("Please pass either p0 or acronym")
        else:
            if acronym is not None:
                print("both p0 and acronym passed, using p0")

        if len(p0) != 3 or not (not isinstance(p0[0], float) and not isinstance(p0[0], int)): 
            raise ValueError("Seed point coordinates should be an array of 3 numbers")

        tract = self.mca.experiment_injection_coordinate_search(seed_point=p0, num_rows=n_experiments, **kwargs)

        if isinstance(tract, str): raise ValueError('Something went wrong with query')
        else:
            return tract
        

if __name__ == "__main__":
    br = ABA()
    tract = br.get_projection_tracts_from_target("PAG", injection_structures=["PAG"], primary_structure_only=True)

    a = 1

