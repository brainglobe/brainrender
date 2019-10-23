import sys
sys.path.append('./')

import os
import pandas as pd
import numpy as np

from allensdk.core.cell_types_cache import CellTypesCache
from allensdk.api.queries.cell_types_api import CellTypesApi

from BrainRender.Utils.paths_manager import Paths
from BrainRender.Utils.data_io import connected_to_internet

class AllenMorphology(Paths):
    def __init__(self, *args, **kwargs):
        if not connected_to_internet():
            raise ConnectionError("You will need to be connected to the internet to use the AllenMorphology class")

        Paths.__init__(self, *args, **kwargs)

        # Create a Cache for the Cell Types Cache API
        self.ctc = CellTypesCache(manifest_file=os.path.join(self.morphology_allen, 'manifest.json'))

        # Get a list of cell metadata for neurons with reconstructions, download if necessary
        self.neurons = pd.DataFrame(self.ctc.get_cells(species=[CellTypesApi.MOUSE], require_reconstruction = True))
        self.n_neurons = len(self.neurons)
        if not self.n_neurons: raise ValueError("Something went wrong and couldn't get neurons metadata from Allen")

        self.downloaded_neurons = self.get_downloaded_neurons()


    def get_downloaded_neurons(self):
        return [os.path.join(self.morphology_allen, f) for f in os.listdir(self.morphology_allen) if ".swc" in f]    

    def download_neurons(self, ids):
        if isinstance(ids, np.ndarray):
            ids = list(ids)
        if not isinstance(ids, (list)): ids = [ids]

        for cellid in ids:
            cell_file = os.path.join(self.morphology_allen, "{}.swc".format(cellid))
            cell = self.ctc.get_reconstruction(cellid, file_name=cell_file)



if __name__ == '__main__':
    AM = AllenMorphology()
    AM.download_neurons(AM.neurons.id.values[:10])
