import os
import numpy as np


"""
    This query URL can be used to download information about ISH experiments from the
    Allen institute:
    url = 'http://api.brain-map.org/api/v2/data/query.json?criteria='+\
            "model::SectionDataSet,"+\
            "rma::criteria,[failed$eqfalse],products[abbreviation$eq'Mouse'],treatments[name$eq'ISH'],"+\
            "rma::include,genes,specimen(donor(age)),plane_of_section"+\
            "&num_rows=50&start_row=0"
    request(url).json()['msg']
"""


def read_raw(filepath):
    """
        reads a .raw file with gene expression data 
        downloaded from the Allen atlas and returns 
        a numpy array with the correct shape.
        See as reference:
            http://help.brain-map.org/display/mousebrain/API#API-Expression3DGridsz

        :param filepath: str or Path object
    """
    filepath = str(filepath)
    if not os.path.isfile(filepath):
        raise ValueError("File doesnt exist")
    if not filepath.endswith(".raw"):
        raise ValueError('Filepath should point to a ".raw" file')

    # Read bytes
    with open(filepath, "rb") as test:
        content = test.read()

    # Create np array and return
    shape = [58, 41, 67]
    data = np.frombuffer(content, dtype="float32").reshape(shape).T
    return data
