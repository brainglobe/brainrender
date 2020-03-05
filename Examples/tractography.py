""" 
    This tutorial shows how download and rendered afferent mesoscale projection data
    using the AllenBrainAtlas (ABA) and Scene classes
"""
import brainrender
brainrender.SHADER_STYLE = 'cartoon'
from brainrender.scene import Scene
from brainrender.Utils.ABA.connectome import ABA


# Create a scene
scene = Scene()

# Get the center of mass of the region of interest
p0 = scene.get_region_CenterOfMass("ZI")

# Get projections to that point
analyzer = ABA()
tract = analyzer.get_projection_tracts_to_target(p0=p0)

# Add the brain regions and the projections to it
scene.add_brain_regions(['ZI'], alpha=.4, use_original_color=True)
scene.add_tractography(tract, display_injection_structure=False, color_by="region")

scene.render()