import sys
sys.path.append('./')

import pandas as pd

from BrainRender.Utils.webqueries import *

def mouselight_api_info():
    # Get infos from the ML API
    url = mouselight_base_url + "graphql"
    # query =  "systemSettings {apiVersion apiRelease neuronCount\}}"
    query =  \
            """
            query {
                queryData {
                    totalCount
                    }
                }
            """
    res =  post_mouselight(url, query=query)
    print("{} neurons on MouseLight database. ".format(res['queryData']['totalCount']))

def mouselight_get_brainregions():
    # Download metadata about brain regions from the ML API
    url = mouselight_base_url + "graphql"
    # query =  "systemSettings {apiVersion apiRelease neuronCount\}}"
    query =  \
            """
            query {
                brainAreas{
                    acronym
                    name
                    id
                    atlasId
                    graphOrder
                    parentStructureId
                    structureIdPath
                }
            }
            """
    res =  post_mouselight(url, query=query)['brainAreas']

    keys = {k:[] for k in res[0].keys()}
    for r in res:
        for k in r.keys():
            keys[k].append(r[k])
    
    structures_data = pd.DataFrame.from_dict(keys)
    return structures_data






