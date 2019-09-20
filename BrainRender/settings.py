import os
import sys

sys.path.append('./')

# Define the folder in which different datasets are saved and where the manifest for the MouseConnectivityCache is saved.
main_fld = "D:\\Dropbox (UCL - SWC)\\Rotation_vte\\analysis_metadata\\anatomy"  # parent folder, all other folders should be within this
connectivity_fld = os.path.join(main_fld, "mouse_connectivity")                 # here is where the MouseConnectivityCache stores experimental data downloaded from the AllenBrainAtlas server
models_fld = "Meshes"                                                           # here is where the .obj with the mesh data for brain structures are saved [first time a structure is used it will be downloaded and saved here]
neurons_fld = os.path.join(main_fld, "Mouse Light")                             # to render 3d models of neurons downloaded from the Mouse Light dataset. Download the JSON from the website and save it here
save_fld =  os.path.join(main_fld, "fc_experiments_unionized")                  # here is where the pandas DataFrame with unionized experiment dat is saved 
rendered_scenes = os.path.join(main_fld, "rendered_scenes")                     # folder where scenes are exported
manifest = os.path.join(connectivity_fld, "manifest.json")  # ! this is what is used by mouseconnectivity cache to check what has been downloaded already


# Check if these folders exist, create them otherwise
folders = [main_fld, connectivity_fld, models_fld, neurons_fld, save_fld]
for fld in folders:
    if not os.path.isdir(fld):
        os.mkdir(fld)
