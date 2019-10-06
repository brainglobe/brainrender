"""
	The code below is work in progress and not yet added to the main body of code.
"""

# import requests
# import pandas as pd
# import numpy as np
# import urllib.request as urlreq
# import urllib.error as urlerr
# import untangle
# import rawpy

# from allensdk.api.queries.mouse_connectivity_cache import MouseConnectivityCache

# import skimage.io as io

# def send_query(query_string, clean=False):
# 	response = requests.get(query_string)
# 	if response.ok:
# 		if not clean:
# 			return response.json()['msg']
# 		else:
# 			return response.json()
# 	else:
# 		raise ValueError("Invalide query string: {}".format(query_string))

# def parse_expid_query(gene_id, orientation=None, **kwargs):
# 	if orientation is None:
# 		query = "http://api.brain-map.org/api/v2/data/query.json?criteria=model::SectionDataSet,rma::criteria,[failed$eq'false'],products[abbreviation$eq'Mouse'],genes[acronym$eq'{}']".format(gene_id)	
# 	elif orientation == 'coronal':
# 		query = "http://api.brain-map.org/api/v2/data/query.json?criteria=model::SectionDataSet,rma::criteria,[failed$eq'false'],products[abbreviation$eq'Mouse'],plane_of_section[name$eq'coronal'],genes[acronym$eq'{}']".format(gene_id)	
# 	elif orientation == 'sagittal':
# 		query = "http://api.brain-map.org/api/v2/data/query.json?criteria=model::SectionDataSet,rma::criteria,[failed$eq'false'],products[abbreviation$eq'Mouse'],plane_of_section[name$eq'sagittal'],genes[acronym$eq'{}']".format(gene_id)	
# 	else:
# 		raise ValueError("Unrecognized value for param orientation")


# 	data = send_query(query)
# 	if not data: raise ValueError("Could not get data")
# 	return data[0]['id'], data[0]

# def download_gene_data(gene_id):
# 	exp_id, metadata = parse_expid_query(gene_id)
# 	query = "http://api.brain-map.org/grid_data/download/{}".format(exp_id)

# 	print("To download expression data, please click on this link:\n{}".format(query))
	
# def get_structure_unionizes(gene_id, **kwargs):
# 	exp_id, metadata = parse_expid_query(gene_id, **kwargs)
# 	query = "http://api.brain-map.org/api/v2/data/query.json?criteria=model::StructureUnionize,rma::criteria,section_data_set[id$eq'{}']".format(exp_id)
# 	return pd.DataFrame(send_query(query))

# def get_all_genes():
# 	# http://api.brain-map.org/api/v2/data/Gene/query.json?only=acronym?num_rows=359625

# 	acronyms = []

# 	startrow = 0
# 	while startrow+2000 < 359625:
# 		query = "http://api.brain-map.org/api/v2/data/Gene/query.json?only=acronym&num_rows=2000&start_row={}".format(startrow)
# 		acronyms.append(pd.DataFrame(send_query(query)).acronym.values)

# 		startrow += 2000
# 	return acronyms

# def get_gene_data(gene_id=None, acronym=None):
# 	if gene_id is not None:
# 		query = "http://api.brain-map.org/api/v2/data/query.json?include=model::Gene[id$eq{}]".format(gene_id)
# 	elif acronym is not None:
# 		query = "http://api.brain-map.org/api/v2/data/query.json?include=model::Gene[acronym$eq'{}']".format(acronym)

# 	data = send_query(query, clean=True)
# 	for i, msg in enumerate(data['msg']):
# 		if i == 0:
# 			temp = {k:[] for k in list(msg.keys())}
		
# 		{temp[k].append(v) for k,v in msg.items()}

# 	print(pd.DataFrame(temp))
# 	return(pd.DataFrame(temp))


# def load_raw_img(filepath):
# 	# raw = rawpy.imread(filepath)
# 	# rgb = raw.postprocess()
# 	# return rgb
# 	sizeGrid = [33, 20, 28] #[132, 80, 114]
# 	img = np.fromfile(filepath, dtype='int16', sep="").reshape([68,40,50])


# 	a = 1

# # gd = get_gene_data(acronym="Vsx1")
# # print(get_structure_unionizes("Vsx1", orientation='sagittal'))

# # expid, _ = parse_expid_query("Vsx1")
# # mapi = MouseAtlasApi()

# # mapi.download_expression_energy("/Users/federicoclaudi/Dropbox (UCL - SWC)/Rotation_vte/analysis_metadata/anatomy", expid)

# # query = "http://mouse.brain-map.org/api/v2/data/query.json?criteria=model::Structure,rma::criteria,structure_sets%5Bid$eq2%5D,pipe::list%5Bxstructures$eq%27id%27%5D,model::SectionDataSet%5Bid$eq70445299%5D,rma::include,genes,plane_of_section,treatments,specimen(donor(age,organism)),probes(orientation,predicted_sequence,forward_primer_sequence,reverse_primer_sequence),products%5Bid$eq1%5D,model::StructureUnionize,rma::criteria,section_data_set%5Bid$eq70445299%5D,rma::include,structure%5Bid$in$xstructures%5D,rma::options%5Bonly$eqid,section_data_set_id,name,expression_energy,acronym,red,green,blue%5D,model::SectionImage%5Bdata_set_id$eq70445299%5D,rma::include,associates,alternate_images,rma::options%5Border$eq%27sub_images.section_number$asc%27%5D,"
# # data = send_query(query)
# # a = 1


# fp = "Examples/example_files/energy.raw"
# # img = load_raw_img(fp)
# mcc = MouseConnectivityCache()


# # get_affine_parameters: https://github.com/AllenInstitute/AllenSDK/blob/57df49c10ef301c84c00000f31abc735819ca141/allensdk/core/mouse_connectivity_cache.py

# a = 1