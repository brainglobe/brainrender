# from brainrender.scene import Scene


# @pytest.fixture
# def scene():
#     return Scene()


# # ---------------------------------------------------------------------------- #
# #                                Mouse specific                                #
# # ---------------------------------------------------------------------------- #


# def test_streamlines():
#     scene = Scene()

#     filepaths, data = scene.atlas.download_streamlines_for_region("CA1")

#     scene.add_brain_regions(["CA1"], use_original_color=True, alpha=0.2)

#     scene.add_streamlines(
#         data, color="darkseagreen", show_injection_site=False
#     )

#     scene.render(camera="sagittal", zoom=1, interactive=False)
#     scene.close()


# def test_streamlines_colored():
#     # Start by creating a scene with the allen brain atlas atlas
#     scene = Scene()

#     # Download streamlines data for injections in the CA1 field of the hippocampus
#     filepaths, data = scene.atlas.download_streamlines_for_region("CA1")

#     scene.add_brain_regions(["CA1"], use_original_color=True, alpha=0.2)

#     # you can pass either the filepaths or the data
#     colors = makePalette(len(data), "salmon", "lightgreen")
#     scene.add_streamlines(data, color=colors, show_injection_site=False)


# def test_neurons():
#     scene = Scene()

#     mlapi = MouseLightAPI()

#     # Fetch metadata for neurons with some in the secondary motor cortex
#     neurons_metadata = mlapi.fetch_neurons_metadata(
#         filterby="soma", filter_regions=["MOs"]
#     )

#     # Then we can download the files and save them as a .json file
#     neurons = mlapi.download_neurons(neurons_metadata[:5])
#     scene.add_neurons(
#         neurons, color="salmon", display_axon=False, neurite_radius=6
#     )


# def test_tractography():
#     scene = Scene()
#     analyzer = ABA()
#     p0 = scene.atlas.get_region_CenterOfMass("ZI")
#     tract = analyzer.get_projection_tracts_to_target(p0=p0)
#     scene.add_tractography(tract, color_by="target_region")

#     scene = Scene()
#     scene.add_tractography(
#         tract, color_by="target_region", VIP_regions=["SCm"], VIP_color="green"
#     )
