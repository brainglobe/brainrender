import sys
import os
from .data_io import load_yaml

class Paths:
    def __init__(self, paths_file = None):
        if paths_file is None:
            self.paths_file = "default_paths.yml"
        else:
            self.paths_file = paths_file

        if not os.path.isfile(paths_file):
            raise FileNotFoundError("Could not find file specifying folder paths: {}".format(self.paths_file))

        # Parse paths file
        paths_dict = load_yaml(paths_file)
        self.folders = paths_dict

        self.mouse_meshes = paths_dict['mouse_meshes']
        self.rat_meshes = paths_dict['rat_meshes']
        self.drosophila_meshes = paths_dict['drosophila_meshes']
        self.other_meshes = paths_dict['other_meshes']
        self.morphology_allen = paths_dict['morphology_allen']
        self.morphology_mouselight = paths_dict['morphology_mouselight']
        self.output_screenshots = paths_dict['output_screenshots']
        self.output_videos = paths_dict['output_videos']
        self.output_scenes = paths_dict['output_scenes']
        self.outpuserut_scenes = paths_dict['user']