import sys
import os

from brainrender.Utils.data_io import save_json

"""
    Class to create and store paths to a number of folders uesed to save/load data
"""


# Default paths for Data Folders (store stuff like object meshes, neurons morphology data etc)
default_paths = dict(
        # BRAIN REGIONS MESHES
        mouse_meshes= "Data/Meshes/Mouse", # allen brain atlas .obj meshes file, downloaded through allen API
        rat_meshes= "Data/Meshes/Rat",    # meshes with rat brain data, to be downloaded
        drosophila_meshes= "Data/Meshes/Drosophila",  # meshes with drosophila brain data, to be downloaded
        other_meshes= "Data/Meshes/Other",  # any other mesh the user might want to store
        metadata= "Data/Metadata",

        # NEURONS MORPHOLOGY
        morphology_allen=  "Data/Morphology/Allen", # .swc files with neurons morphology downloaded through allen API
        morphology_cache= "Data/Morphology/cache",
        morphology_mouselight= "Data/Morphology/MouseLight", # .swc and .json files from mouse light dataset

        # Allen caches
        mouse_connectivity_cache= "Data/ABA/MCC",
        mouse_celltype_cache= "Data/ABA/MCTC",
        annotated_volume = "Data/ABA",

        mouse_connectivity_volumetric="Data/ABA/Volumetric",
        mouse_connectivity_volumetric_cache="Data/ABA/Volumetric/cache",
        
        # Streamlines cache
        streamlines_cache= "Data/Streamlines",

        # OUTPUT Folders
        output_screenshots= "Output/Screenshots",
        output_videos= "Output/Videos",
        output_scenes= "Output/Scenes",
        output_data= "Output/Data",

        # User folder
        user= "User",
)


class Paths:
    _folders = ["mouse_meshes", "other_meshes", "morphology_allen", "morphology_cache",
                "morphology_mouselight", "mouse_connectivity_cache", "mouse_celltype_cache", 
                "streamlines_cache", "output_screenshots", "output_videos", 
                "output_scenes", "output_data", "user", "metadata", 'annotated_volume', 
                'mouse_connectivity_volumetric', 'mouse_connectivity_volumetric_cache']

    def __init__(self, base_dir=None, **kwargs):
        """
        Parses a YAML file to get data folders paths. Stores paths to a number of folders used throughtout brainrender. 
        Other classes (e.g. brainrender.Scene) subclass Paths.
        
        :param base_dir: str with path to directory to use to save data. If none the user's base directiry is used. 
        :param kwargs: use the name of a folder as key and a path as argument to specify the path of individual subfolders
        """
        # Get and make base directory
        if base_dir is None:
            user_dir = os.path.expanduser("~")
            if not os.path.isdir(user_dir):
                raise FileExistsError("Could not find user base folder (to save brainrender data). Platform: {}".format(sys.platform))
            self.base_dir = os.path.join(user_dir, ".brainrender")
        else:
            self.base_dir = base_dir

        if not os.path.isdir(self.base_dir):
            os.mkdir(self.base_dir)

        for fld_name in self._folders:
            # Check if user provided a path for this folder, otherwise use default
            fld_path = kwargs.pop(fld_name, default_paths[fld_name])

            # Make complete path and save it as an attribute of this class
            path = os.path.join(self.base_dir, fld_path)

            # Create folder if it doesn't exist 
            if not os.path.isdir(path):
                print("Creating folder at: {}".format(path))
                os.makedirs(path)
            self.__setattr__(fld_name, path)


        # Make a file for morphology cache metadata
        self.morphology_cache_metadata = os.path.join(self.morphology_cache, 'metadata.json')
        if not os.path.isfile(self.morphology_cache_metadata):
            save_json(self.morphology_cache_metadata, {})