sagittal_camera = {
    "pos": (5976, 6290, 29737),
    "focalPoint": (6588, 3849, -5688),
    "viewup": (0, -1, 0),
    "distance": 35514,
    "clippingRange": (24098, 49971),
}

sagittal_camera2 = {
    "pos": (9782, 1795, -40999),
    "focalPoint": (6588, 3849, -5688),
    "viewup": (0, -1, 0),
    "distance": 35514,
    "clippingRange": (23256, 51031),
}


frontal_camera = {
    "pos": (-19199, -1428, -5763),
    "focalPoint": (9157, 4406, -5858),
    "viewup": (0, -1, 0),
    "distance": 28950,
    "clippingRange": (19531, 40903),
}

top_camera = {
    "pos": (7760, -31645, -5943),
    "focalPoint": (6588, 3849, -5688),
    "viewup": (-1, 0, 0),
    "distance": 35514,
    "clippingRange": (27262, 45988),
}

top_side_camera = {
    "pos": (4405, -31597, -5411),
    "focalPoint": (6588, 3849, -5688),
    "viewup": (0, 0, -1),
    "distance": 35514,
    "clippingRange": (26892, 46454),
}

three_quarters_camera = {
    "pos": (-20169, -7298, 14832),
    "focalPoint": (6588, 3849, -5688),
    "viewup": (0, -1, 0),
    "distance": 35514,
    "clippingRange": (16955, 58963),
}

cameras = dict(
    sagittal=sagittal_camera,
    sagittal2=sagittal_camera2,
    frontal=frontal_camera,
    top=top_camera,
    top_side=top_side_camera,
    three_quarters=three_quarters_camera,
)
