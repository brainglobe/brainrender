"""
    Developing code to visualise atlases from:
        https://scalablebrainatlas.incf.org/index.php
"""

from vtkplotter import load

from brainrender.Utils.data_io import load_json, load_volume_file, listdir


class SBA(Paths):
    def __init__(self, atlas_folder):
        """
            :param atlas_folder: path to folder with atlas data. The folder content must include:
                    - volumetric data (e.g. as .nii)
                    - label to acronym look up file (lbl_to_acro.json)
                    - label to rgb look up file (lbl_to_rgb.json)
                    - label to full name look up file (lbl_to_name.json)

                    Optionally the folder can contain a .obj file with the root (whole brain) mesh
        """

        Paths.__init__(self)

        # Get folder content
        if not os.path.isdir(atlas_folder):
            raise FileNotFoundError(f"The folder passed doesn't exist: {atlas_folder}")

        content = listdir(atlas_folder)
        if not [f for f in content if f.endswith('.nii')]: # TODO expand to support multiple formats
            raise ValueError("Could not find volumetric data")

        if not [f for f in content if "lbl_to_acro.json" in content]:
            raise FileNotFoundError("Could not find file with label to acronym lookup")

        if not [f for f in content if "lbl_to_rgb.json" in content]:
            raise FileNotFoundError("Could not find file with label to color lookup")

        if not [f for f in content if "lbl_to_name.json" in content]:
            raise FileNotFoundError("Could not find file with label to full name lookup")

        self.lbl_to_acro_lookup = load_json([f for f in content if "lbl_to_acro.json" in content][0])
        self.lbl_to_rgb_lookup = load_json([f for f in content if "lbl_to_rgb.json" in content][0])
        self.lbl_to_name_lookup = load_json([f for f in content if "lbl_to_name.json" in content][0])

        self.volume_data = load_volume_file([f for f in content if f.endswith('.nii')])

        if [f for f in content if f.endswith(".obj")]:
            if len([f for f in content if f.endswith(".obj")]) > 1:
                raise ValueError("Found too many obj file")
            self.root = load([f for f in content if f.endswith(".obj")][0])
