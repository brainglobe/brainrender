import sys
sys.path.append('./')   # <- necessary to import packages from other directories within the project

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from collections import namedtuple
from vtkplotter import Plotter, show, interactive, Video, settings, Sphere, shapes

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


# ! TODO write function to get 3d MESH points, centroid etc...

class BrainRender:
    hemispheres = namedtuple("hemispheres", "left right both") # left: CONTRA, right: IPSI
    hemispheres_names = ["left", "right", "both"]
    
    # useful vars for analysis
    projection_metric = "projection_energy"
    volume_threshold = 0.5
    excluded_regions = ["fiber tracts"]

    # frequently used structures
    main_structures = ["PAG", "SCm", "ZI", "SCs", "GRN"]

    def __init__(self):
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


    def get_structure_location(self, acronym):
        struct = self.structure_tree.get_structures_by_acronym([acronym])[0]
        experiments = self.mcc.get_experiments(cre=False,  injection_structure_ids=[struct["id"]])
        x, y, z  = [], [], []
        for exp in experiments:
            x.append(exp["injection_x"])
            y.append(exp["injection_y"])
            z.append(exp["injection_z"])

        return [np.nanmean(x).astype(np.int32), np.nanmean(y).astype(np.int32), np.nanmean(z).astype(np.int32)]

    def get_projection_tracts_to_target(self, acronym=None, p0=None):
        if p0 is None:
            if acronym is not None:
                p0 = self.get_structure_location(acronym)
            else: raise ValueError("Please pass either p0 or acronym")
        else:
            if acronym is not None:
                warnings.warn("both p0 and acronym passed, using p0")

        tract = self.mca.experiment_spatial_search(seed_point=p0)

        if isinstance(tract, str): raise ValueError('Something went wrong with query')
        else:
            return tract

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
        """[look at all areas projecting to it]
        
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

            experiment_data = pd.read_pickle(os.path.join(self.save_fld, "{}.pkl".format(origin_acronym)))
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

    def plot_structures_3d(self, structures_acronyms, default_colors=True, verbose=False, target=None, target_color=[.4, .4, .4], others_color=[.4, .4, .4],
                        others_alpha=1, sagittal_slice=False, neurons_file=None, render=True, neurons_kwargs={}, specials=[], notebook=False):
        if structures_acronyms is None: structures_acronyms = []
        
        # Download OBJ files
        for structure_id in structures_acronyms:
            structure = self.structure_tree.get_structures_by_acronym([structure_id])

            obj_file = os.path.join(self.models_fld, "{}.obj".format(structure[0]["acronym"]))
            if not os.path.isfile(obj_file):
                mesh = self.space.download_structure_mesh(structure_id = structure[0]["id"], ccf_version ="annotation/ccf_2017", 
                                                file_name=obj_file)

        # Create plot
        vp = Plotter(title='first example')

        # plot whole brain
        obj_path = os.path.join(self.models_fld, "root.obj")
        root = vp.load(obj_path, c=[.8, .8, .8], alpha=.3)  


        # Plot target structure
        if target is not None:
            obj_path = os.path.join(self.models_fld, "{}.obj".format(target))
            if not os.path.isfile(obj_file):
                mesh = self.space.download_structure_mesh(structure_id = structure[0]["id"], ccf_version ="annotation/ccf_2017", 
                                                file_name=obj_file)

            target_mesh = vp.load(obj_path, c=target_color, alpha=1)

 
        # plot other brain regions
        other_structures = []
        for i, structure in enumerate(structures_acronyms):
            if target is not None:
                if structure == target: continue
            structure = self.structure_tree.get_structures_by_acronym([structure])

            if default_colors:
                color = [x/255 for x in structure[0]["rgb_triplet"]]
            else: 
                if isinstance(others_color[0], list):
                    color = others_color[i]
                else:
                    color = others_color

            if structure[0]["acronym"] in specials:
                color = "steelblue"
                alpha = 1
            else:
                alpha = others_alpha

            obj_path = os.path.join(self.models_fld, "{}.obj".format(structure[0]["acronym"]))
            mesh = vp.load(obj_path, c=color, alpha=alpha) 
            other_structures.append(mesh)

            if verbose:
                print("Rendering: {} - ({})".format(structure[0]["name"], structure[0]["acronym"]))

        if sagittal_slice:
            for a in vp.actors:
                a.cutWithPlane(origin=(0,0,6000), normal=(0,0,-1), showcut=True)


        # add neurons
        if neurons_file is not None:
            neurons_actors = render_neurons(neurons_file, **neurons_kwargs)
        else:
            neurons_actors = []

        # Add sliders
        if target is not None:
            def target_slider(widget, event):
                value = widget.GetRepresentation().GetValue()
                target_mesh.alpha(value)

            vp.addSlider2D(target_slider, xmin=0.01, xmax=0.99, value=0.5, pos=4, title="target alpha")

        def others_slider(widget, event):
            value = widget.GetRepresentation().GetValue()
            for actor in other_structures:
                actor.alpha(value)
        vp.addSlider2D(others_slider, xmin=0.01, xmax=0.99, value=0.5, pos=3, title="others alpha")

        # Add inset 
        inset = root.clone().scale(.5)
        inset.alpha(1)
        vp.showInset(inset, pos=(0.9,0.2))

        if render:
            if notebook:
                plt.show()
            else:
                show(*vp.actors, *neurons_actors, interactive=True, roll=180, azimuth=-35, elevation=-25)  
        else:
            show(*vp.actors, *neurons_actors, interactive=0, offscreen=True, roll=180)  

        return vp

    def video_maker(self, dest_path, vp=None, *args, **kwargs):
        if vp is None: 
            vp = self.plot_structures_3d(*args, render=False, **kwargs)

        fld, video = os.path.split(dest_path)
        os.chdir(fld)
        video = Video(name=video, duration=3)
        
        for i  in range(80):
            vp.show()  # render the scene first
            vp.camera.Azimuth(2)  # rotate by 5 deg at each iteration
            # vp.camera.Zoom(i/40)
            video.addFrame()
        video.close()  # merge all the recorded frames

    def render_injection_sites(self, experiments, *args, structures=None, vp=None, render=True, **kwargs):
        if structures is None: structures = []

        if vp is None:
            vp = self.plot_structures_3d(structures, *args, render=False, **kwargs)

        injection_sites = []
        for exp in experiments:
            injection_sites.append(Sphere(pos=(
                    exp["injection_x"], exp["injection_y"], exp["injection_z"]),
                    r = 500*exp["injection_volume"], c=[.2, .6, .2]
                    ))

        if render:
            show(*vp.actors, *injection_sites,  interactive=True)  
        else:
            show(*vp.actors, *injection_sites,  interactive=False, offscreen=True)  
        return vp

    def render_tractography(self, tracts, *args, render=True, vp=None, **kwargs):
        # tracts should have the traces for 1 experiment only
        if vp is None:
            vp = self.plot_structures_3d(*args, render=False, **kwargs)

        actors = []
        for i, t in enumerate(tracts):
            actors.append(Sphere(pos=t['injection-coordinates'], r=150*t['injection-volume']))

            points = [p['coord'] for p in t['path']]
            actors.append(shapes.Tube(points, r=20, c='red', alpha=1, res=12))

        if render:
            show(*vp.actors, *actors, interactive=1)  
        else:
            show(*vp.actors, *actors, interactive=0, offscreen=True)  
        return vp


if __name__ == "__main__":
    # rendere settings
    settings.useOpenVR = False



    analyzer = BrainRender()


    SOI = "PAG"
    n_structures = 0

    neurons = os.path.join(analyzer.neurons_fld, "neurons_in_PAG.json")
    # efferents = analyzer.analyze_efferents(SOI, projection_metric="normalized_projection_volume")
    vp = analyzer.plot_structures_3d(["SCm", "PAG", "ZI", "GRN", "CUN", "PPN"], verbose=True, sagittal_slice=False,
                                    default_colors=False,
                                    target = None,
                                    target_color="red",
                                    others_color="palegoldenrod",
                                    others_alpha=0.5, 
                                    neurons_file = neurons,
                                    render=True, 
                                    specials=["PAG"],
                                    neurons_kwargs={'neurite_radius':25})


    # videopath = os.path.join(analyzer.main_fld, "pagneuron.mp4")
    # analyzer.video_maker(videopath, vp=vp)


