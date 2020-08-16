from brainrender.Utils.atlases_utils import get_neurons


class MPin:
    """
        Extends brainrender's Atlas class with functionality
        specific to BrainGlobe's mpin_zfish_1um atlas.

        This class uses morphapi's mpin_api MpinMorphologyAPI
        to download and render neurons registered to the
        zebra fish atlass
    """

    def get_neurons(self, *args, **kwargs):
        """
        Gets rendered morphological data of neurons reconstructions downloaded using
        morphapi's MpinMorphologyAPI. 

        Accepts neurons argument as:
            - file(s) with morphological data
            - vedo mesh actor(s) of entire neurons reconstructions
            - dictionary or list of dictionary with actors for different neuron parts

        :param neurons: str, list, dict. File(s) with neurons data or list of rendered neurons.
        :param display_axon, display_dendrites: if set to False the corresponding neurite is not rendered
        :param color: default None. Can be:
                - None: each neuron is given a random color
                - color: rbg, hex etc. If a single color is passed all neurons will have that color
                - cmap: str with name of a colormap: neurons are colored based on their sequential order and cmap
                - dict: a dictionary specifying a color for soma, dendrites and axon actors, will be the same for all neurons
                - list: a list of length = number of neurons with either a single color for each neuron
                        or a dictionary of colors for each neuron
        :param alpha: float in range 0,1. Neurons transparency
        :param neurite_radius: float > 0 , radius of tube actor representing neurites
        :param use_cache: bool, if True a cache is used to avoid having to crate a neuron's mesh anew, otherwise a new mesh is created
        """

        return get_neurons(*args, **kwargs)
