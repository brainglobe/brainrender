sagittal_camera = {
    "position": (5976, 6290, 29737),
    "focal": (6588, 3849, -5688),
    "viewup": (0, -1, 0),
    "distance": 35514,
    "clipping": (24098, 49971),
    "orientation": (4, 1, 177),
}

sagittal_camera2 = {
    "position": (9782, 1795, -40999),
    "focal": (6588, 3849, -5688),
    "viewup": (0, -1, 0),
    "distance": "35514",
    "clipping": (23256, 51031),
    "orientation": (-3, -175, -179),
}


frontal_camera = {
    "position": (-19199, -1428, -5763),
    "focal": (9157, 4406, -5858),
    "viewup": (0, -1, 0),
    "distance": 28950,
    "clipping": (19531, 40903),
    "orientation": (-12, 90, -180),
}

top_camera = {
    "position": (7760, -31645, -5943),
    "focal": (6588, 3849, -5688),
    "viewup": (-1, 0, 0),
    "distance": 35514,
    "clipping": (27262, 45988),
    "orientation": (-88, -102, 169),
}

top_side_camera = {
    "position": (4405, -31597, -5411),
    "focal": (6588, 3849, -5688),
    "viewup": (0, 0, -1),
    "distance": 35514,
    "clipping": (26892, 46454),
    "orientation": (-86, 83, -97),
}

three_quarters_camera = {
    "position": (-20169, -7298, 14832),
    "focal": (6588, 3849, -5688),
    "viewup": (0, -1, 0),
    "distance": 35514,
    "clipping": (16955, 58963),
    "orientation": (-18, 53, 175),
}

cameras = dict(
    sagittal=sagittal_camera,
    sagittal2=sagittal_camera2,
    frontal=frontal_camera,
    top=top_camera,
    top_side=top_side_camera,
    three_quarters=three_quarters_camera,
)
