import os
import sys

sys.path.append('./')

# Define the folder in which different datasets are saved and where the manifest for the MouseConnectivityCache is saved.
folders_paths = {}
folders_paths['main_fld'] = "/Users/federicoclaudi/Dropbox (UCL - SWC)/Rotation_vte/analysis_metadata/anatomy/"  # parent folder, all other folders should be within this
folders_paths['connectivity_fld'] = os.path.join(folders_paths['main_fld'], "mouse_connectivity")                 # here is where the MouseConnectivityCache stores experimental data downloaded from the AllenBrainAtlas server
folders_paths['models_fld'] = "Meshes"                                                           # here is where the .obj with the mesh data for brain structures are saved [first time a structure is used it will be downloaded and saved here]
folders_paths['neurons_fld'] = os.path.join(folders_paths['main_fld'], "Mouse Light")                             # to render 3d models of neurons downloaded from the Mouse Light dataset. Download the JSON from the website and save it here
folders_paths['save_fld'] =  os.path.join(folders_paths['main_fld'], "fc_experiments_unionized")                  # here is where the pandas DataFrame with unionized experiment dat is saved 
folders_paths['rendered_scenes'] = os.path.join(folders_paths['main_fld'], "rendered_scenes")                     # folder where scenes are exported
folders_paths['manifest'] = os.path.join(folders_paths['connectivity_fld'], "manifest.json")  # ! this is what is used by mouseconnectivity cache to check what has been downloaded already
folders_paths['output_fld'] = os.path.join(folders_paths['main_fld'], "output")               # This is where screenshots and videos will be saved


# Check if these folders exist, create them otherwise
def make_folders(folders_paths):
  folders = ["main_fld", "connectivity_fld", "models_fld", "neurons_fld", "save_fld"]
  for fld in folders:
      if not os.path.isdir(folders_paths[fld]):
          os.mkdir(folders_paths[fld])


def update_folders(main_fld):
  folders_paths = {}
  folders_paths['main_fld'] = main_fld
  folders_paths['connectivity_fld'] = os.path.join(folders_paths['main_fld'], "mouse_connectivity")                 
  folders_paths['models_fld'] = "Meshes"                                                           
  folders_paths['neurons_fld'] = os.path.join(folders_paths['main_fld'], "Mouse Light")                             
  folders_paths['save_fld'] =  os.path.join(folders_paths['main_fld'], "fc_experiments_unionized")                  
  folders_paths['rendered_scenes'] = os.path.join(folders_paths['main_fld'], "rendered_scenes")                     
  folders_paths['manifest'] = os.path.join(folders_paths['connectivity_fld'], "manifest.json")  
  folders_paths['output_fld'] = os.path.join(folders_paths['main_fld'], "output")
  return folders_paths


if __name__ == "__main__":
    make_folders(folders_paths)
