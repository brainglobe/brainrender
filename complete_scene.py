"""
    Trying to test as many features of `Scene` as possible in
    one script.
"""

from brainrender.scene import Scene
import brainrender
from brainrender import ruler

brainrender.SHADER_STYLE = "cartoon"
brainrender.SHOW_AXES = True

scene = Scene(title="Test Scene")

# # add brain regions
mos, hy = scene.add_brain_regions(["MOs", "HY"], alpha=0.2)
mos.wireframe()
hy.wireframe()

# # Get center of mass of the two regions
p1 = scene.atlas.get_region_CenterOfMass("MOs")
p2 = scene.atlas.get_region_CenterOfMass("HY")
scene.add_sphere_at_point(p1, radius=200)

# Add a ruler form the brain surface
scene.add_ruler_from_surface(p2, unit_scale=0.001)

# Add a ruler between the two regions
scene.add_actor(ruler(p1, p2, unit_scale=0.001, units="mm"))

# Cut with plane
stn = scene.add_brain_regions("STR", hemisphere="right").alpha(0.4)
hy = scene.add_brain_regions("HY")
scene.cut_actors_with_plane("sagittal", actors=hy)

# Fake render
scene.render(interactive=False)

# Add more regions and silhouettes
ca1 = scene.add_brain_regions("CA1")
scene.add_silhouette(ca1)

visp = scene.add_brain_regions("VISp", add_labels=False).lw(1).alpha(0.3)
scene.add_sphere_at_point(
    scene.atlas.get_region_CenterOfMass("VISp"), radius=200
)
p3 = scene.atlas.get_region_CenterOfMass("VISp")
scene.add_sphere_at_point(p3, radius=200)


# add labels
# scene.add_actor_label(ca1, "CA1")

# Add some random stuff
scene.add_optic_cannula("VISp")
scene.add_plane("sagittal")


# final render
scene.list_actors(extensive=True)
scene.render()
