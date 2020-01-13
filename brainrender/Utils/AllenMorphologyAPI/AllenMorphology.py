import sys
sys.path.append('./')

import os
import pandas as pd
import numpy as np

from allensdk.core.cell_types_cache import CellTypesCache
from allensdk.api.queries.cell_types_api import CellTypesApi
from allensdk.core.swc import Morphology

from brainrender.Utils.paths_manager import Paths
from brainrender.Utils.data_io import connected_to_internet

"""
    WORK IN PROGRESS

    This class should handle the download and visualisation of neuronal morphology data from the Allen database.
"""


class AllenMorphology(Paths):
    """ Handles the download and visualisation of neuronal morphology data from the Allen database. """

    def __init__(self, *args, **kwargs):
        """
            Initialise API interaction and fetch metadata of neurons in the Allen Database. 
        """
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
        """ 
            Get's the path to files of downloaded neurons
        """
        return [os.path.join(self.morphology_allen, f) for f in os.listdir(self.morphology_allen) if ".swc" in f]    

    def download_neurons(self, ids):
        """
            Download neurons

        :param ids: list of integers with neurons IDs

        """
        if isinstance(ids, np.ndarray):
            ids = list(ids)
        if not isinstance(ids, (list)): ids = [ids]

        for neuron_id in ids:
            neuron_file = os.path.join(self.morphology_allen, "{}.swc".format(neuron_id))
            neuron = self.ctc.get_reconstruction(neuron_id, file_name=neuron_file)




if __name__ == '__main__':
    AM = AllenMorphology()
    AM.download_neurons(AM.neurons.id.values[:10])
