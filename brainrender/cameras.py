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
    "position": (-28926, 3609, -5802),
    "focal": (6588, 3849, -5688),
    "viewup": (0, -1, 0),
    "distance": 35514,
    "clipping": (21933, 52696),
    "orientation": (0, 90, -180),
}

top_camera = {
    "position": (5854, -31645, -4865),
    "focal": (6587, 3850, -5803),
    "viewup": (-1, 0, 0),
    "distance": "35514",
    "clipping": (27222, 46030),
    "orientation": (-88, 38, -51),
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
    "position": (-28926, 3609, -5802),
    "focal": (6588, 3849, -5688),
    "viewup": (0, -1, 0),
    "distance": 35514,
    "clipping": (21933, 52696),
    "orientation": (0, 90, -180),
}

cameras = dict(
    sagittal=sagittal_camera,
    sagittal2=sagittal_camera2,
    frontal=frontal_camera,
    top=top_camera,
    top_side=top_side_camera,
    three_quarters=three_quarters_camera,
)
