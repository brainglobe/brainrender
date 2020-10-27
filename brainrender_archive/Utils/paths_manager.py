import sys
import os

"""
    Class to create and store paths to a number of folders uesed to save/load data
"""


# Default paths for Data Folders (store stuff like object meshes, neurons morphology data etc)
default_paths = dict(
    # OUTPUT Folders
    output_screenshots="Output/Screenshots",
    output_videos="Output/Videos",
    output_data="Output/Data",
    # Allen caches
    mouse_connectivity_cache="Data/ABA/MCC",
    annotated_volume_fld="Data/ABA",
    mouse_connectivity_volumetric="Data/ABA/Volumetric",
    mouse_connectivity_volumetric_cache="Data/ABA/Volumetric/cache",
    gene_expression_cache="Data/ABA/Volumetric/GeneExpressionCache",
    # Streamlines cache
    streamlines_cache="Data/Streamlines",
    ibdb_meshes_folder="Data/InsectsDBs",
)


class Paths:
    _folders = list(default_paths.keys())

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
                raise FileExistsError(
                    "Could not find user base folder (to save brainrender data). Platform: {}".format(
                        sys.platform
                    )
                )
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
