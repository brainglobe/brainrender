import vtk

reader = vtk.vtkSTLReader()
reader.SetFileName("skull.stl")


sphere = vtk.vtkSuperquadricSource()
sphere.ToroidalOn()
sphere.SetThetaResolution(50)
sphere.SetPhiResolution(50)

mapper = vtk.vtkOpenGLPolyDataMapper()
mapper.SetInputConnection(sphere.GetOutputPort())

mapper.SetVertexShaderCode("""
    #version 330

    uniform mat4 modelViewMatrix;
    uniform mat4 modelMatrix;
    uniform mat4 viewMatrix;
    uniform mat4 projectionMatrix;
    uniform mat4 textureMatrix;
    uniform mat4 modelViewProjectionMatrix;
    uniform mat4 normalMatrix;

    in vec4 position;
    in vec4 color;
    in vec4 normal;
    in vec2 texcoord;
    
    in vec3 n;
    in vec3 l;

    void propFuncVS(void)
    {
        n = normalize(normal);
        l = vec3(modelViewMatrix * vec4(n,0));
        position = modelViewProjectionMatrix * position;
    }
""")

actor = vtk.vtkActor()
actor.SetMapper(mapper)

renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.SetSize(500, 500)
renderWindow.AddRenderer(renderer)
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

renderer.AddActor(actor)

renderWindow.Render()
renderWindowInteractor.Start()
