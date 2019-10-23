

from allensdk.core.cell_types_cache import CellTypesCache
from allensdk.api.queries.cell_types_api import CellTypesApi
from allensdk.core.cell_types_cache import ReporterStatus as RS

# download all cells
ctc = CellTypesCache(manifest_file='manifest.json')

cells = ctc.get_cells()
print("Total cells: %d" % len(cells))

# mouse cells
cells = ctc.get_cells(species=[CellTypesApi.MOUSE])
print("Mouse cells: %d" % len(cells))

# human cells
cells = ctc.get_cells(species=[CellTypesApi.HUMAN])
print("Human cells: %d" % len(cells))

# cells with reconstructions
cells = ctc.get_cells(require_reconstruction = True)
print("Cells with reconstructions: %d" % len(cells))

# all cre positive cells
cells = ctc.get_cells(reporter_status = RS.POSITIVE)
print("Cre-positive cells: %d" % len(cells))

# cre negative cells with reconstructions
cells = ctc.get_cells(require_reconstruction = True, 
                      reporter_status = RS.NEGATIVE)
print("Cre-negative cells with reconstructions: %d" % len(cells))

