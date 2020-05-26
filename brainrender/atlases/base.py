import pandas as pd
import numpy as np
import os
from vtkplotter import Plane, Mesh


from brainrender.Utils.paths_manager import Paths
from brainrender.Utils.data_manipulation import get_coords


class Atlas(Paths):
    """
    This class is the base structure for an Atlas class. Atlas-specific class will need to
    inherit from this class and re-define crucial methods to support scene creation.  
    """

    atlas_name = "BASE"
    mesh_format = 'vtk' # or obj, stl etc..

    # These variables are generally useful but need to be specified for each atlas
    _root_midpoint = [None, None, None] # 3d coordinates of the CoM of root mesh
    _planes_norms = dict( # normals of planes cutting through the scene along
                        # orthogonal axes. These values must be replaced if atlases
                        # are oriented differently.
                        sagittal = [0, 0, 1],
                        coronal = [1, 0, 0],
                        horizontal = [0, 1, 0],
    )
    _root_bounds = [[], # size of bounding boox around atlas' root along each direction 
                    [], 
                    []]

    default_camera = None # Replace this with a camera params dict to specify a default camera for your atlas

    def __init__(self, base_dir=None, **kwargs):
        """ 
        Set up file paths
        
        :param base_dir: path to directory to use for saving data (default value None)
        :param kwargs: can be used to pass path to individual data folders. See brainrender/Utils/paths_manager.py

        """
        # Specify atlas specific paths
        Paths.__init__(self, base_dir=base_dir, **kwargs)
        self.meshes_folder = None # where the .obj mesh for each region is saved


        # Get some atlas specific data 
        # ! REPLACE these in the init method of your atlas
        self.annotated_volume = None
                                # A 3d image with a scalar label at each region indicating
                                # which brain region each voxel corresponds to

        self.regions = None
                # list of all regions in the atlas
        self.region_acronyms = None   

    def print_structures(self):
        """ 
        Prints the name of every structure in the structure tree to the console.
        """
        if isinstance(self.regions, list) and isinstance(self.region_acronyms, list):
            print([f"{a} - {n}" for a,n in zip(self.region_acronyms, self.regions)], sep="\n")

    # ---------------------------------------------------------------------------- #
    #                             General atlas methods                            #
    # ---------------------------------------------------------------------------- #
    # ---------------------------------- Planes ---------------------------------- #
    # functions to create oriented planes that can be used to slice actors etc
    def get_plane_at_point(self, pos, norm, sx, sy, 
                        color='lightgray', alpha=.25,
                     **kwargs):
        """ 
            Returns a plane going through a point at pos, oriented 
            orthogonally to the vector norm and of width and height
            sx, sy. 

            :param pos: 3-tuple or list with x,y,z, coords of point the plane goes through
            :param sx, sy: int, width and height of the plane
            :param norm: 3-tuple or list with 3d vector the plane is orthogonal to
            :param color, alpha: plane color and transparency
        """
        plane = Plane(pos=pos, normal=norm, 
                    sx=sx, sy=sy, c=color, alpha=alpha)
        return plane

    def get_sagittal_plane(self, pos=None,  **kwargs):
        """
            Creates a Plane actor centered at the midpoint of root (or a user given locatin)
            and oriented along the sagittal axis

            :param pos: if not None, passe a list of 3 xyz defining the position of the 
                            point the plane goes through.
        """
        if pos is None: 
            pos = self._root_midpoint
            if pos[0] is None:
                raise ValueError(f"The atlases _root_midpoint attribute is not specified")
        elif not isinstance(pos, (list, tuple)) or not len(pos)==3:
            raise ValueError(f"Invalid pos argument: {pos}")

        norm = self._planes_norms['sagittal']
        sx = float(np.diff(self._root_bounds[0]))
        sy = float(np.diff(self._root_bounds[1]))

        sx += sx/5
        sy += sy/5
        sag_plane = self.get_plane_at_point(pos, norm, sx, sy, **kwargs)

        return sag_plane

    def get_horizontal_plane(self, pos=None,  **kwargs):
        """
            Creates a Plane actor centered at the midpoint of root (or a user given locatin)
            and oriented along the horizontal axis

            :param pos: if not None, passe a list of 3 xyz defining the position of the 
                            point the plane goes through.
        """
        if pos is None: 
            pos = self._root_midpoint
            if pos[0] is None:
                raise ValueError(f"The atlases _root_midpoint attribute is not specified")
        elif not isinstance(pos, (list, tuple)) or not len(pos)==3:
            raise ValueError(f"Invalid pos argument: {pos}")

        norm = self._planes_norms['horizontal']
        sx = float(np.diff(self._root_bounds[2]))
        sy = float(np.diff(self._root_bounds[0]))

        sx += sx/5
        sy += sy/5
        hor_plane = self.get_plane_at_point(pos, norm, sx, sy, **kwargs)

        return hor_plane

    def get_coronal_plane(self, pos=None,  **kwargs):
        """
            Creates a Plane actor centered at the midpoint of root (or a user given locatin)
            and oriented along the coronal axis

            :param pos: if not None, passe a list of 3 xyz defining the position of the 
                            point the plane goes through.
        """
        if pos is None: 
            pos = self._root_midpoint
            if pos[0] is None:
                raise ValueError(f"The atlases _root_midpoint attribute is not specified")
        elif not isinstance(pos, (list, tuple)) or not len(pos)==3:
            raise ValueError(f"Invalid pos argument: {pos}")

        norm = self._planes_norms['coronal']
        sx = float(np.diff(self._root_bounds[2]))
        sy = float(np.diff(self._root_bounds[1]))

        sx += sx/5
        sy += sy/5
        cor_plane = self.get_plane_at_point(pos, norm, sx, sy, **kwargs)

        return cor_plane


    # ---------------------------------------------------------------------------- #
    #                       Methods to support Scene creation                      #
    # ---------------------------------------------------------------------------- #
    """
        These methods are used by brainrender.scene to populate a scene using
        the Allen brain atlas meshes. 
        You will need to overwrite these methods when you define your atlas class. 
        Not all methods are required for all atlases, but the fewer methods you have
        the less you can do with your atlas.
    """

    # -------------------------- Getting regions/neurons ------------------------- #
    def _check_obj_file(self, structure, obj_file):
        """
        If the .obj file for a brain region hasn't been downloaded/created already, 
        this function downloads it and saves it.

        :param structure: string, acronym of brain region
        :param obj_file: path to .obj file to save downloaded data.

        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'_check_obj_file' method!")

    def _get_structure_mesh(self, acronym,  **kwargs):
        """
        Fetches the mesh for a brain region from the Allen Brain Atlas SDK.

        :param acronym: string, acronym of brain region
        :param **kwargs:
        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'_get_structure_mesh' method!")

    def get_region_unilateral(self, region, hemisphere="both", color=None, alpha=None):
        """
        Regions meshes are loaded with both hemispheres' meshes by default.
        This function splits them in two.

        :param region: str, actors of brain region
        :param hemisphere: str, which hemisphere to return ['left', 'right' or 'both'] (Default value = "both")
        :param color: color of each side's mesh. (Default value = None)
        :param alpha: transparency of each side's mesh.  (Default value = None)

        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'get_region_unilateral' method!")

    @staticmethod
    def add_brain_regions(self, *agrs, **kwargs):
        """
			Adds brain regions meshes to scene.
			Check the atlas' method to know how it works
		"""
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'add_brain_regions' method!")


    @staticmethod # static because it inherits from scene
    def add_neurons(self, neurons,  **kwargs):
        """
        Adds rendered morphological data of neurons reconstructions 
        For more details about argument look at each atlases' method
        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'add_neurons' method!")
        
    @staticmethod # static method because it inherits from scene
    def add_neurons_synapses(self, neurons,  **kwargs):
        """
        Adds the location of synapses.
        For more details about argument look at each atlases' method
        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'add_neurons_synapses' method!")

    # -------------------------- Parents and descendants ------------------------- #
    def get_structure_ancestors(self, regions, ancestors=True, descendants=False):
        """
        Get's the ancestors of the region(s) passed as arguments

        :param regions: str, list of str with acronums of regions of interest
        :param ancestors: if True, returns the ancestors of the region  (Default value = True)
        :param descendants: if True, returns the descendants of the region (Default value = False)

        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'get_structure_ancestors/get_structure_descendants' methods!")

    def get_structure_descendants(self, regions):
        return self.get_structure_ancestors(regions, ancestors=False, descendants=True)

    def get_structure_parent(self, acronyms):
        """
        Gets the parent of a brain region (or list of regions) from the hierarchical structure of the
        Allen Brain Atals.

        :param acronyms: list of acronyms of brain regions.

        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'get_structure_parent' method!")

    # ----------------------------------- Utils ---------------------------------- #
    def get_region_color(self, regions):
        """
        Gets the RGB color of a brain region from the Allen Brain Atlas.

        :param regions:  list of regions acronyms.

        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'get_structure_parent' method!")

    @staticmethod
    def _check_valid_region_arg(region):
        """
        Check that the string passed is a valid brain region name.
        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'get_structure_parent' method!")

    def get_structure_from_coordinates(self, p0, just_acronym=True):
        """
        Given a point in the Allen Mouse Brain reference space, returns the brain region that the point is in. 

        :param p0: list of floats with XYZ coordinates. 

        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'get_structure_from_coordinates' method!")
    
    def get_colors_from_coordinates(self, p0):
        """
            Given a point or a list of points returns a list of colors where 
            each item is the color of the brain region each point is in
        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'get_colors_from_coordinates' method!")

    def get_hemisphere_from_point(self, point):
        """
            Given a point it checks in which hemisphere the point is.
            Depends on self._root_midpoint
        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'get_hemisphere_from_point' method!")

    def get_hemispere_from_point(self, p0):
        """
            Given a point it returns the corresponding point on the other hemisphere
        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'get_hemispere_from_point' method!")

    def mirror_point_across_hemispheres(self, point):
        """
            Given a point it returns the coordinates of the corresponding point in the other hemisphere
            Depends on self._root_midpoint
        """
        raise NotImplementedError(f"Your atlas {self.atlas_name} doesn't support" +
                    "'mirror_point_across_hemispheres' method!")

    def get_region_CenterOfMass(self, regions, unilateral=True, hemisphere="right"):
        """
        Get the center of mass of the 3d mesh of one or multiple brain regions.

        :param regions: str, list of brain regions acronyms
        :param unilateral: bool, if True, the CoM is relative to one hemisphere (Default value = True)
        :param hemisphere: str, if unilteral=True, specifies which hemisphere to use ['left' or 'right'] (Default value = "right")
        :returns: coms = {list, dict} -- [if only one regions is passed, then just returns the CoM coordinates for that region.
                                If a list is passed then a dictionary is returned. ]
        """

        if not isinstance(regions, list):
            regions = [regions]

        coms = {}
        for region in regions:
            # Check if input is an actor or if we need to load one
            if isinstance(region, Mesh):
                mesh = region
            else:
                # load mesh corresponding to brain region
                if unilateral:
                    mesh = self.get_region_unilateral(region, hemisphere="left")
                else:
                    mesh = self._get_structure_mesh(region)
            com =  mesh.centerOfMass()

            #  if using right hemisphere, mirror COM
            if unilateral and hemisphere.lower() == 'right':
                com = self.mirror_point_across_hemispheres(com)
            
            coms[region] = com

        # return data
        if len(coms.keys()) == 1:
            return com
        elif len(coms.keys()) == 0:
            return None
        else:
            return coms