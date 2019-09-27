import requests

# http://help.brain-map.org/display/mousebrain/API#API-Expression3DGrids



def send_query(query_string) -> dict: # ! from https://github.com/efferencecopy/ecallen/blob/master/ecallen/images.py
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


def get_experiments_ids_by_genes(genes):
    # # model query: http://api.brain-map.org/api/v2/data/query.xml?criteria=
    #             model::SectionDataSet,
    #             rma::criteria,[failed$eq'false'],products[abbreviation$eq'Mouse'],plane_of_section[name$eq'coronal'],genes[acronym$eq'Adora2a']
    if not isinstance(genes, list): genes = [genes]

    ids = {}
    for gene in genes:
        if not isinstance(gene, str): raise ValueError("Invalide value for gene: {}".format(gene))

        query = "http://api.brain-map.org/api/v2/data/query.xml?criteria=model::SectionDataSet,rma::criteria,[failed$eq'false'],products[abbreviation$eq'Mouse'],plane_of_section[name$eq'sagittal'],genes[acronym$eq'{}']".format(gene)
        response = send_query(query)
        print(response)


def query_allen_api(exp_id):
    if not isinstance(exp_id, int): raise ValueError("Invalid exp id: {}".format(exp_id))



if __name__ == "__main__":
    get_experiments_ids_by_genes("chx10")