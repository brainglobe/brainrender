from myterial import salmon_dark
from oneibl.onelight import ONE
import numpy as np
from random import choices
import sys
from rich import print
from pathlib import Path


from brainrender import Scene, Animation
from brainrender.actors import Points
from brainrender.cameras import cameras

sys.path.append("./")
from paper.figures import INSET

print("[bold red]Running: ", Path(__file__).name)

# define camera positions
cam0 = {
    "pos": (7264, 2794, 23463),
    "viewup": (0, -1, 0),
    "clippingRange": (17971, 43355),
    "focalPoint": (6588, 3849, -5688),
    "distance": 29178,
}
cam1 = {
    "pos": (6746, 3258, 18418),
    "viewup": (0, -1, 0),
    "clippingRange": (13256, 37840),
    "focalPoint": (6588, 3849, -5688),
    "distance": 24114,
}

# --------------------------------- callback --------------------------------- #


def spiker(scene, framen, tot_frames, cam1=None, cam2=None, end=1, prev=0):
    """
    Update channels meshes based on which channels
    deteted spikes
    """
    if framen%15 == 0:  # update only every .5s
        # Remove previous spikes
        spikes = scene.get_actors(name="spikes")
        spikes_sil = scene.get_actors(name="spikes silhouette")
        scene.remove(*spikes, *spikes_sil)

        # turn on current spikes
        # select spikes for this frame
        t0 = (framen * max_t) / tot_frames
        t1 = ((framen + 1) * max_t) / tot_frames
        idxs = np.where((spikes_times >= t0) & (spikes_times < t1))[0]

        # get cluster -> channel -> probe location
        clusts = spikes_clu[choices(idxs, k=1000)].ravel()
        chs = clu_channel[clusts].ravel().astype(np.int64)
        points = probes_locs.iloc[chs]

        # add to scene
        spheres = Points(
            points[["ccf_ap", "ccf_dv", "ccf_lr"]].values,
            colors=salmon_dark,
            alpha=1,
            radius=36,
            name="spikes",
        )
        spheres = scene.add(spheres)
        scene.add_silhouette(spheres, lw=LW + 1)

    # Interpolate cameras
    anim.segment_fact = (end - framen) / (end - prev)
    cam = anim._interpolate_cameras(cam1, cam2)
    return cam


# ------------------------------- create scene ------------------------------- #

scene = Scene(inset=INSET, screenshots_folder="paper/screenshots")
scene.root._needs_silhouette = True
scene.add_brain_region("TH", "MOs", alpha=0.6, silhouette=True)


# download and process probe data
one = ONE()
one.set_figshare_url("https://figshare.com/articles/steinmetz/9974357")

# select session
sessions = one.search(["trials"])
sess = sessions[7]  # 3

# Get spikes data
probes_locs = one.load_dataset(sess, "channels.brainLocation")
clu = one.load_dataset(sess, "clusters")
clu_probes = one.load_dataset(sess, "clusters.probes")
clu_channel = one.load_dataset(sess, "clusters.peakChannel")

spikes_clu = one.load_dataset(sess, "spikes.clusters")
spikes_times = one.load_dataset(sess, "spikes.times")
max_t = np.max(spikes_times)

# Render probes
k = int(len(probes_locs) / 374.0)
for i in range(k):
    points = probes_locs[i * 374 : (i + 1) * 374]

    color = "#adadac"
    alpha = 1
    LW = 1

    spheres = Points(
        points[["ccf_ap", "ccf_dv", "ccf_lr"]].values,
        colors=color,
        alpha=alpha,
        radius=30,
    )
    spheres = scene.add(spheres, names="probe")
    scene.add_silhouette(spheres, lw=LW)


# --------------------------------- Animation -------------------------------- #
anim = Animation(scene, "videos", "probes", size=None)
fps = 30

anim.add_keyframe(
    0,
    duration=7,
    callback=spiker,
    zoom=1.9,
    cam1=cameras["three_quarters"],
    cam2=cam0,
    end=int(fps * 7),
    prev=0,
)
anim.add_keyframe(
    7,
    duration=0.3,
    camera="sagittal",
    callback=spiker,
    zoom=1.9,
    cam1=cam0,
    cam2=cam0,
    end=int(fps * 7.3),
    prev=int(fps * 7),
)
anim.add_keyframe(
    7.3,
    duration=2.7,
    camera="sagittal",
    callback=spiker,
    zoom=1.9,
    cam1=cam0,
    cam2=cam1,
    end=int(fps * 10),
    prev=int(fps * 7.3),
)

anim.make_video(duration=10, fps=fps)
