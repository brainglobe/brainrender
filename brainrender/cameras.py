sagittal_camera = dict(
    position=[5532.562, 8057.256, 66760.941],
    focal=[6587.835, 3849.085, 5688.164],
    viewup=[0.045, -0.997, 0.061],
    distance=24893.917,
    clipping=[9826.898, 43920.235],
)

sagittal_camera2 = dict(
    position=(10705.845660949382, 7435.678067378925, -36936.3695486442),
    focal=(6779.790352916297, 3916.3916231239214, 5711.389387062087),
    viewup=(-0.0050579179155257475, -0.9965615097647067, -0.08270172139591858),
    distance=42972.44034956088,
    clipping=(30461.81976236306, 58824.38622122339),
)


coronal_camera = dict(
    position=[-54546.708, 526.426, 6171.914],
    focal=[6587.835, 3849.085, 5688.164],
    viewup=[0.054, -0.999, -0.002],
    distance=61226.68,
    clipping=[47007.899, 79272.88],
)

top_camera = dict(
    position=[1482.128, -57162.314, 5190.803],
    focal=[6587.835, 3849.085, 5688.164],
    viewup=[-0.996, 0.083, 0.016],
    distance=61226.68,
    clipping=[52067.13, 72904.35],
)


three_quarters_camera = dict(
    position=[-27271.044, -18212.523, 51683.47],
    focal=[6587.835, 3849.085, 5688.164],
    viewup=[0.341, -0.921, -0.19],
    distance=61226.68,
    clipping=[42904.747, 84437.903],
)

cameras = dict(
    sagittal=sagittal_camera,
    sagittal2=sagittal_camera2,
    coronal=coronal_camera,
    top=top_camera,
    three_quarters=three_quarters_camera,
)
