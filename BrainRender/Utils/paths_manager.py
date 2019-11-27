import sys
import os
from .data_io import load_yaml

class Paths:
    def __init__(self, paths_file=None):
        """[Parses a YAML file to get data folders paths]
        
        Keyword Arguments:
            path_file {[str]} -- [Path to a YAML file specifying paths to data folders, to replace default paths] (default: {None})
        """
        if paths_file is None:
            self.paths_file = "default_paths.yml"
        else:
            self.paths_file = paths_file

        if not os.path.isfile(self.paths_file):
            raise FileNotFoundError("Could not find file specifying folder paths: {}".format(self.paths_file))

        # Parse paths file
        paths_dict = load_yaml(self.paths_file)
        self.folders = paths_dict

        self.mouse_meshes = paths_dict['mouse_meshes']
        self.rat_meshes = paths_dict['rat_meshes']
        self.drosophila_meshes = paths_dict['drosophila_meshes']
        self.other_meshes = paths_dict['other_meshes']
        self.morphology_allen = paths_dict['morphology_allen']
        self.morphology_cache = paths_dict['morphology_cache']
        self.morphology_mouselight = paths_dict['morphology_mouselight']
        
        self.mouse_connectivity_cache = paths_dict['mouse_connectivity_cache']
        self.mouse_celltype_cache = paths_dict['mouse_celltype_cache']

        self.streamlines_cache = paths_dict['streamlines_cache']

        self.output_screenshots = paths_dict['output_screenshots']
        self.output_videos = paths_dict['output_videos']
        self.output_scenes = paths_dict['output_scenes']
        self.output_data = paths_dict['output_data']

        self.user = paths_dict['user']
        self.metadata = paths_dict['metadata']

        # Create folders if they don't exist
        for fld in list(self.folders.values()):
            if not os.path.isdir(fld):
                print("Creating folder at: {}".format(fld))
                os.makedirs(fld)
