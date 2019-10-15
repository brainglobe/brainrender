import vtk



# This creates a donut mesh
sphere = vtk.vtkSuperquadricSource()
sphere.ToroidalOn()
sphere.SetThetaResolution(50)
sphere.SetPhiResolution(50)

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(sphere.GetOutputPort())

# If you want to set the opacity in the shader to anything lower than 1,
# make sure you SetOpacity to something below 1 too, or it will be treated as opaque
actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetOpacity(1)

# Handle the rendering and interaction
ren = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)



# And tell the actor property that it should totally use this cool program
openGLproperty = actor.GetProperty()


# openGLproperty.SetAmbient(0) # default 0
# openGLproperty.SetDiffuse(1) # defautl: 1

# openGLproperty.SetEdgeVisibility(1) # defualt 0 
# openGLproperty.SetEdgeColor([1, 0, 0])
# openGLproperty.SetRenderLinesAsTubes(1)
# openGLproperty.SetLineWidth(5) # -> 1

# openGLproperty.GetLighting() # def True
# openGLproperty.GetLineWidth() # -> 1
# openGLproperty.GetShading() # -> 0


actor.ForceTr()


# Add the actor and set a nice bg color
ren.AddActor(actor)
ren.SetBackground(0.3, 0, 0.4)
ren.SetBackground2(0.1, 0, 0.2)
ren.SetGradientBackground(1)

print("ready")
iren.Initialize()
ren.GetActiveCamera().SetPosition(0, -1, 0)
ren.GetActiveCamera().SetViewUp(0, 0, 1)
ren.ResetCamera()
renWin.Render()
iren.Start()