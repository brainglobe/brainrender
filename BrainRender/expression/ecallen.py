# code from: https://github.com/efferencecopy/ecallen

"""
The ecallen.images module handles interactions with Allen API.
Copyright (C) 2017 Charlie Hass charlie@efferencecopy.net
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import requests
import numpy as np
import os
import urllib.request as urlreq
import urllib.error as urlerr
from PIL import Image
Image.MAX_IMAGE_PIXELS = 1000000000
import io
import skimage.io as skio
from skimage.measure import label, regionprops
from skimage.filters import threshold_otsu
from skimage import dtype_limits
import os
from tqdm import tqdm

def send_query(query_string) -> dict:
    """
    Send a query to the Allen API.
    send_query(query_string)
    Args:
        query_string: string
            A string used as an API query for the Allen Institute API.
            Typeically this will be generated automatically by the
            function query_string_builder
    Returns:
        json_tree: dict
            contains the results of the query
    """
    # send the query, package the return argument as a json tree
    response = requests.get(query_string)
    if response.ok:
        json_tree = response.json()
        if json_tree['success']:
            return json_tree
        else:
            exception_string = 'did not complete api query successfully'
    else:
        exception_string = 'API failure. Allen says: {}'.format(
            response.reason)

    # raise an exception if the API request failed
    raise ValueError(exception_string)


def query_string_builder(query_type, **kwargs) -> str:
    """
    Build an API query string.
    query_string_builder(query_type, kwargs)
    Constructs a string that can be used as an API query for the
    Allen Institute for brain science.
    Args:
        query_type : string
            This string defines the query type. Possible options include:
            "section_dataset_info"
            "section_image_ids"
            "section_image_download"
            "affine_3d"
            "affine_2d"
            "xy_to_pir_slow"
    Optional Args
        section_data_set_id : int
        section_image_id : int
        x_pix : int
        y_pix : int
    Returns:
        query_string : string
            Can be used as an API request
    """
    # TODO: convert this constrcut to a dictionary, or build class "query_type"
    if query_type.lower() == "section_dataset_info":
        query_string = ('/data/query.json?criteria='
                        'model::SectionDataSet'
                        ',rma::criteria,[id$eq{}]'
                        ',rma::include,genes,plane_of_section,probes'
                        ',products,reference_space,specimen,treatments'
                        )
        query_string = query_string.format(kwargs['section_data_set_id'])

    elif query_type.lower() == "section_image_ids":
        query_string = ('/data/query.json?criteria='
                        'model::SectionImage'
                        ',rma::criteria,[data_set_id$eq{}]'
                        )
        query_string = query_string.format(kwargs['section_data_set_id'])

    elif query_type.lower() == "section_image_download":
        query_string = '/section_image_download/{}'
        query_string = query_string.format(kwargs['section_image_id'])

    elif query_type.lower() == "affine_3d":
        query_string = ('/data/query.json?criteria='
                        'model::SectionDataSet'
                        ',rma::criteria,[id$eq{}],rma::include,alignment3d'
                        )
        query_string = query_string.format(kwargs['section_data_set_id'])

    elif query_type.lower() == "affine_2d":
        query_string = ('/data/query.json?criteria='
                        'model::SectionImage'
                        ',rma::criteria,[id$eq{}],rma::include,alignment2d')
        query_string = query_string.format(kwargs['section_image_id'])

    elif query_type.lower() == "xy_to_pir_slow":
        query_string = '/image_to_reference/{}.json?x={}&y={}'
        query_string = query_string.format(kwargs['section_image_id'],
                                           kwargs['x_pix'],
                                           kwargs['y_pix'])

    else:
        query_string = ''

    # join the prefix and query type
    allen_url = 'http://api.brain-map.org/api/v2'
    query_string = "{}{}".format(allen_url, query_string)

    return query_string


def get_imaging_params(data_set_id) -> dict:
    """
    Retrieve metadata for a section_dataset.
    get_imaging_params(data_set_id)
    retrieve a dictionary of image metadata for a single experiment
    Args:
        data_set_id: int
            The id of the section_data_set
    Returns:
        dictionary of parameters and values
    """
    # send the request
    query_string = query_string_builder("section_dataset_info",
                                        section_data_set_id=data_set_id)
    json = send_query(query_string)

    # define the image params
    img_params = {
        'plane_of_section': json['msg'][0]['plane_of_section']['name'],
        'red_channel': json['msg'][0]['red_channel'],
        'green_channel': json['msg'][0]['green_channel'],
        'blue_channel': json['msg'][0]['blue_channel'],
        'is_FISH': json['msg'][0]['treatments'][0]['name'].lower() == 'fish',
        'is_ISH': json['msg'][0]['treatments'][0]['name'].lower() == 'ish',
        'probes': [dct['acronym'].lower() for dct in json['msg'][0]['genes']],
        'section_thickness': json['msg'][0]['section_thickness'],
        'genotype': json['msg'][0]['specimen']['name']
    }
    return img_params


def get_affine_3d(data_set_id) -> dict:
    """
    Get the coefficients for 3D affine transformation.
    get_affine_3d(data_set_id)
    Query the Allen API to obtain the values for the TVR transform. This
    converts section_image 'volume' coordinates to 'reference' coordinates.
    Args:
        data_set_id: int
                Scalar that identifies the data set
    Returns:
        affine3: dict
                With the following keys:
                'A_mtx': 3x3 matrix of affine rotation coefficients
                'traslation': 1x3 vector of translation coefficients
                'section_thickness':  brain slice thickness in um (float)
    """
    query_string = query_string_builder('affine_3d',
                                        section_data_set_id=data_set_id)
    json_tree = send_query(query_string)
    align_info = json_tree['msg'][0]['alignment3d']
    coeffs = [align_info['tvr_{:0>2}'.format(x)] for x in range(12)]

    # construct the output dictionary
    affine3 = {'A_mtx': np.array(coeffs[0:9]).reshape((3, 3)),
               'translation': np.array(coeffs[9:]).reshape((3, 1)),
               'section_thickness': json_tree['msg'][0]['section_thickness']}

    return affine3


def get_affine_2d(image_id) -> dict:
    """
    Get the coefficients for 2D affine transformation.
    get_affine_2d(section_data_set_id)
    Query the Allen API to obtain the values for the TVR transform. This
    converts section_image 'volume' coordinates to 'reference' coordinates.
    Args:
        image_id: (int) Scalar that identifies the data set
    Returns:
        affine2: dict
                With the following keys:
                'A_mtx': 2x2 matrix of affine rotation coefficients
                'traslation': 1x2 vector of translation coefficients
                'section_number': (int) used to determine distance between
                                  different slices
    """
    # send the query, extract the alignment information
    query_string = query_string_builder('affine_2d', section_image_id=image_id)
    json_tree = send_query(query_string)
    align_info = json_tree['msg'][0]['alignment2d']
    coeffs = [align_info['tsv_{:0>2}'.format(x)] for x in range(6)]

    # construct the output dictionary
    affine2 = {'A_mtx': np.array(coeffs[0:4]).reshape((2, 2)),
               'translation': np.array(coeffs[4:]).reshape((2, 1)),
               'section_number': json_tree['msg'][0]['section_number']}

    return affine2


def xy_to_pir(x_pix, y_pix, section_data_set_id, section_image_id) -> np.array:
    """
    Convert from [X,Y] to [P,I,R] coordinates.
    xy_to_pir(x_pix, y_pix, section_data_set_id, section_image_id)
    Implement 2D and 3D affine transformations to convert from
    "image" coordinates to section coordinates, and then to the
    Common Coordinate Framework units.
    Args:
        x_pix: numpy.array
                vector of X coordinates of pixels in a section_image
        y_pix: numpy.array
                vector of Y coordinates of pixels in a section_image
        section_data_set_id: int
        section_image_id: int
    Returns:
        pir: numpy.array
            [Posterior, Inferior, Right] of the corresponding location in the
            common coordinate framework (CCF) in units of micrometers
    """
    # implement the 2D affine transform for image_to_section coordinates
    t_2d = get_affine_2d(section_image_id)
    tmtx_tsv = np.hstack((t_2d['A_mtx'], t_2d['translation']))
    tmtx_tsv = np.vstack((tmtx_tsv, [0, 0, 1]))  # T matrix for 2D affine
    data_mtx = np.vstack((x_pix, y_pix, np.ones_like(x_pix)))  # [3 x Npix]
    xy_2d_align = np.dot(tmtx_tsv, data_mtx)

    # implement the 3D affine transform for section_to_CCF coordinates
    t_3d = get_affine_3d(section_data_set_id)
    tmtx_tvr = np.hstack((t_3d['A_mtx'], t_3d['translation']))
    tmtx_tvr = np.vstack((tmtx_tvr, [0, 0, 0, 1]))

    data_mtx = np.vstack((xy_2d_align[0, :],
                         xy_2d_align[1, :],
                         np.ones((1, xy_2d_align.shape[1])) * t_2d['section_number'] * t_3d['section_thickness'],
                         np.ones((1, xy_2d_align.shape[1]))))

    xyz_3d_align = np.dot(tmtx_tvr, data_mtx)
    pir = xyz_3d_align[0:3, :]
    return pir


def retrieve_file_over_http(apistring, file_path) -> None:
    """
    Download and save an image from the Allen Institute.
    retrieve_file_over_http(apistring, file_path)
    Retrieve a file from the Allen Database using HTTP and save
    the file to the local hard disk
    Args:
        apistring: string
        file_path: string
             Absolute path including the file name to save.
    This file was copied (almost) verbatim from the Allen API SDK
    and was accessed at the following URL:
    https://alleninstitute.github.io/AllenSDK/_modules/allensdk/api/api.html#Api.retrieve_file_over_http
    I modified the usage of urllib2 into urllib (for python 3+)
    """
    try:
        with open(file_path, 'wb') as f:
            response = urlreq.urlopen(apistring)
            f.write(response.read())
    except urlerr.HTTPError:
        print("Couldn't retrieve file from\n  %s" % apistring)


def get_all_section_image_ids(data_set_id) -> list:
    """
    Retrieve all of the section image IDs for a section_dataset.
    get_all_section_image_ids(data_set_id)
    Retrieve all section_image IDs that are from a single brain
    (section_data_set) by querying the Allen API
    Args:
        data_set_id: (int) The ID for an ABI section_data_set
    Returns:
        list of section_image IDs
    """

    # query the Allen API to obtain the section_image IDs
    # that correspond with this data set
    query_string = query_string_builder('section_image_ids',
                                        section_data_set_id=data_set_id)
    json_tree = send_query(query_string)
    return [x['id'] for x in json_tree['msg']]


def save_all_section_images(data_set_id, data_directory=None) -> None:
    """
    Save all section images from a single section_dataset (brain).
    save_all_section_images(data_set_id, data_directory)
    Downloads all images from a single brain and saves them to the local
    hard disk.
    Args:
        data_set_id: int
        data_directory: string
                        The full path to the directory where the images will
                        be saved
    """
    # TODO make test case for downloading all images of well known dataset

    # store the starting directory
    starting_dir = os.getcwd()

    # cd to the data directory.
    # If a sub-directory for this dataset does not exist, make one
    if data_directory is not None:
        data_directory = os.path.expanduser(data_directory)  # tilde expansion
        os.chdir(data_directory)

    new_dir_name = str(data_set_id)
    if new_dir_name not in os.listdir('.'):
        os.mkdir(new_dir_name)
    os.chdir(new_dir_name)

    # query the Allen API to obtain the section_image IDs
    # that correspond with this dataset
    section_image_ids = get_all_section_image_ids(data_set_id)

    # download any images that do not currently exist in the local database
    print("Downloading the following images from data set: %d" % data_set_id)
    print(section_image_ids)

    existing_files = os.listdir('.')
    for img_id in tqdm(section_image_ids):
        fname = "{}.jpg".format(img_id)
        if fname not in existing_files:
            save_section_image(img_id, img_file_name=fname)

    #  change directories back to the initial directory
    os.chdir(starting_dir)
    print("Finished downloading images")

    return None


def save_section_image(section_image_id, img_file_name=None) -> None:
    """
    Save a single section_image.
    save_section_image(section_image_id, img_file_name)
    Saves an image to the local hard disk
    Args:
        section_image_id: int
        img_file_name: string (optional, default = "section_image_[id]")
    """
    # create default file name if one was not given
    if img_file_name is None:
        img_file_name = 'section_image_' + section_image_id

    apistring = query_string_builder("section_image_download",
                                     section_image_id=section_image_id)
    fpath = os.path.join(os.getcwd(), img_file_name)
    retrieve_file_over_http(apistring, fpath)
    return None


def get_section_image(section_image_id, savepath=None) -> np.array:
    """
    Download a section image (without saving to disk).
    get_section_image(section_image_id)
    Download an image from the Allen Institute for local processing
    but do not save to disk
    Args:
        section_image_id: int
    Returns:
        img: np.array
    """
    apistring = query_string_builder("section_image_download",
                                     section_image_id=section_image_id)
    response = requests.get(apistring)
    response.raise_for_status()
    with io.BytesIO(response.content) as f:
        img = Image.open(f)
        if savepath is not None:
            # savename, ext = os.path.split(savepath)
            img.save(savepath)
        return np.array(img)


def extract_region_props(img, params, 
                         section_dataset_id,
                         probes,
                         ish_minval=70
                         ) ->list:
    """Segment neuron cell bodies via thresholding.
    Accepts images from the Allen Brain Institute (ISH or FISH) and segments
    fluorescently labeled neuron cell bodies. Segmentation is accomplished by
    computing a label matrix on the thresholded image (via Otsu's method).
    Args:
        img (np.array): image.
        section_dataset_id (int): The experiment ID specified by the
            Allen Brain Institute.
        probes (list): list of strings, specifying the RNA target of the
            ISH or FISH stain
        ish_minval (int): applies to ISH images only. Any value below
            this will be ignored by the thresholding algorithm.
            Default value is 70.
    Returns:
        rprops (list): each element is a dictionary of region properties
            as defined by scikit-image's regionprops function
    """
    # user must specify probe(s) (i.e., color channels) to analyze
    # if only one probe is specified, turn it into a list
    if type(probes) != list and type(probes) == str:
        probes = [probes]

    probe_ch = [
        params['red_channel'].lower() in probes,
        params['green_channel'].lower() in probes,
        params['blue_channel'].lower() in probes,
    ]

    if params['is_FISH']:
        n_ch_correct = sum(probe_ch) > 0 and sum(probe_ch) <= 3
        assert n_ch_correct, "Did not identify the correct number of channels"
        img = np.array(img[:, :, probe_ch]).max(axis=2)  # max project

        # measure threshold
        thresh = threshold_otsu(img, nbins=256)

    elif params['is_ISH']:
        img = dtype_limits(img)[1] - img  # invert
        assert sum(probe_ch) == 3, "Not all ISH color channels identical"
        img = np.max(img, axis=2)  # max project inverted image

        # measure threshold
        thresh = threshold_otsu(img[img > ish_minval], nbins=256)

    else:
        raise ValueError('Image is neither FISH nor ISH')

    # apply the threshold to the image, which is now just a 2D matrix
    bw = img > thresh

    # label image regions with an integer. Each region gets a unique integer
    label_image = label(bw)
    rprops = regionprops(label_image)

    return rprops