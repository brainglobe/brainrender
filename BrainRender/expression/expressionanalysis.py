import sys
sys.path.append("./")

from BrainRender.expression.ecallen import *
from BrainRender.settings import *

import random
from tqdm import tqdm


class ExpressionAnalyser:
    def __init__(self, exp_id=None, save_imgs=True):
        self.exp_id = exp_id
        self.save_imgs = save_imgs

    def _get_correct_id(self, exp_id):
        if exp_id is not None:
            return exp_id
        if exp_id is None and self.exp_id is not None:
            return self.exp_id
        else: 
            raise ValueError("ExpressionAnalyser wasnt passed any experiment id")

    def get_experiment_images_ids(self, exp_id=None):
        exp_id = self._get_correct_id(exp_id)
        exp_images_ids = get_all_section_image_ids(exp_id)
        self.exp_images_ids = exp_images_ids
        return exp_images_ids

    def get_experiment_images(self, exp_id=None, save_imgs=None):
        if save_imgs is None:
            save_imgs = self.save_imgs

        exp_imgs = self.get_experiment_images_ids(exp_id)
        imgs = []

        # see if the images have already been saved
        if os.path.isdir(os.path.join(folders_paths['save_fld'], str(exp_id))):
            # The folder exists, see if images are saved there
            for imgid in tqdm(exp_imgs):
                filename = os.path.join(folders_paths['save_fld'], str(exp_id), "{}.png".format(imgid))
                if os.path.isfile(filename):
                    imgs.append(np.load(filename))
                else:
                    img = get_section_image(imgid, savepath=filename)
                    imgs.append(img)
        else:
            os.mkdir(os.path.join(folders_paths['save_fld'], str(exp_id)))
            print("Fetching {} images for experiment id: {}".format(len(exp_imgs), exp_id))
            for imgid in tqdm(exp_imgs):
                filename = os.path.join(folders_paths['save_fld'], str(exp_id), "{}.png".format(imgid))
                img = get_section_image(imgid, savepath=filename)
                imgs.append(img)
        return imgs

    def get_experiment_metadata(self, exp_id=None):
        exp_id = self._get_correct_id(exp_id)
        params = get_imaging_params(exp_id)
        self.params = params
        return params

    def get_cells(self, exp_id=None, N=None):

        exp_id = self._get_correct_id(exp_id)
        
        print("Fetching data and metadata")
        images_ids = self.get_experiment_images_ids(exp_id)
        images = self.get_experiment_images(exp_id)
        metadata = self.get_experiment_metadata(exp_id)

        print("Got data. Extracting cells coordinates")
        cells = []
        for imgid, img in tqdm(zip(images_ids, images)):
            rprops = extract_region_props(img,
                                exp_id,
                                metadata['probes'])

            # grab the X and Y pixels at the center of each labeled region
            cell_x_pix = np.array([roi['centroid'][1] for roi in rprops])
            cell_y_pix = np.array([roi['centroid'][0] for roi in rprops])

            # register cells
            pir = xy_to_pir(cell_x_pix,
                            cell_y_pix,
                            exp_id,
                            imgid)

            img_cells = [[x, y, z] for x, y, z in zip(pir[0], pir[1], pir[2])]
            cells.extend(img_cells)
        
        if N is None:
            print("Task completed, found {} cells for experiment id: {}".format(len(cells), exp_id))
            self.cells = cells
        else:
            tot_cells = len(cells)
            cells = self.get_n_cells(cells, N)
            print("Task completed, found {} cells for experiment id: {}. Returning {} randomly selected cells".format(len(cells), exp_id, N))
            self.cells = cells
        return cells

    def get_n_cells(self, cells, N):
        if not isinstance(cells, (list, tuple)):
            raise ValueError("cells argument must be a list")
        if not isinstance(N, int):
            raise ValueError("N must be an integer")
        return random.choices(cells, k=N)