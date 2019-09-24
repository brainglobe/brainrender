from allensdk.api.queries.ontologies_api import OntologiesApi
from allensdk.api.queries.reference_space_api import ReferenceSpaceApi
from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi

# oapi = OntologiesApi()
# space = ReferenceSpaceApi()


def get_brain_structure_from_cooords(p0):
    mca = MouseConnectivityApi()
    data = mca.experiment_injection_coordinate_search(seed_point=p0, primary_structure_only=True, num_rows=1)