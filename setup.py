from setuptools import setup, find_namespace_packages

requirements = [
    "numpy",
    "pandas",
    "vtkplotter",
    "vtk",
    "jupyter",
    "allensdk",
    "k3d",
    "tqdm",
    "pyyaml",
    "scikit-image",
    "brainio",
    "gzip",
]

setup(
    name="BrainRender",
    version="0.1.0",
    description="Python scripts to use Allen Brain Map data for analysis "
                "and rendering",
    install_requires=requirements,
    python_requires=">=3.6",
    packages=find_namespace_packages(exclude=(
        "Installation", "Meshes", "Metadata", "Screenshots")),
    include_package_data=True,
    url="https://github.com/BrancoLab/BrainRender",
    author="Federico Claudi",
    zip_safe=False,
)
