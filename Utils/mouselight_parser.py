import os
import json
from vtkplotter import *
import pandas as pd
from tqdm import tqdm
import numpy as np

def render_neurons(ml_file, colors_l = None, neurite_radius=10):
    def neurites_parser(neurites, color, soma):
        def get_zyx(data):
            if len(data) == 0: raise ValueError

            try:
                z,y,x =  data["z"].values[0], data["y"].values[0], data["x"].values[0]
            except:
                z,y,x = data["z"], data["y"], data["x"]

            if not isinstance(z, float): raise ValueError
            else: return z,y,x

        parent_counts = neurites["parentNumber"].value_counts()
        branching_points = parent_counts.loc[parent_counts > 1]

        # loop over each branching point
        tubes = []
        for idx, bp in branching_points.iteritems():
            bp = neurites.loc[neurites.sampleNumber == idx]
            post_bp = neurites.loc[neurites.parentNumber == idx]
            
            # loop on each branc
            for bi, branch in post_bp.iterrows():
                parent = neurites.loc[neurites.sampleNumber == branch.parentNumber]
                if parent.parentNumber.values[0] == -1:
                    granparent = soma
                else:
                    granparent = neurites.loc[neurites.sampleNumber == parent.parentNumber.values[0]]
                branch_points = [get_zyx(granparent), get_zyx(parent), get_zyx(bp), get_zyx(branch)]

                
                # loop over all following points
                idx = branch.sampleNumber
                while True:
                    nxt = neurites.loc[neurites.parentNumber == idx]
                    if len(nxt) != 1: 
                        break
                    else:
                        branch_points.append(get_zyx(nxt))
                        idx += 1

                if len(branch_points) < 2: # plot either a line between two branch_points or  a spheere
                    tubes.append(Sphere(branch_points[0], c="g", r=100))
                    continue 

                try:
                    tube = shapes.Tube(branch_points, r=neurite_radius, c=color, alpha=1, res=24)
                except:
                    raise ValueError
                tubes.append(tube)
            
        return tubes


    # Load the data
    with open(ml_file) as f:
        data = json.load(f)

    data = data["neurons"]
    print("Found {} neurons".format(len(data)))

    # Loop over neurons
    actors = []
    for neuron in tqdm(data):
        soma_coords = neuron["soma"]
        soma = Sphere(pos=[soma_coords["z"], soma_coords["y"], soma_coords["x"]], c=[.8, .8, .8], r=neurite_radius*3)
        actors.append(soma)

        # Draw dendrites
        dendrites = neurites_parser(pd.DataFrame(neuron["dendrite"]), [.8, .4, .4], soma_coords)
        axons = neurites_parser(pd.DataFrame(neuron["axon"]), [.4, .8, .4], soma_coords)

        actors.extend(dendrites)
        actors.extend(axons)

    return actors


def test():
    """
        Small function used to test the render_neurons function above
    """
    neurons = os.path.join(r"D:\Dropbox (UCL - SWC)\Rotation_vte\analysis_metadata\anatomy\Mouse Light", "axons_in_PAG.json")

    res = render_neurons(neurons)

    vp = Plotter(title='first example')
    vp.show(*res)
    

if __name__ == "__main__":
    test()