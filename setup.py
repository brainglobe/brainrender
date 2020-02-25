from setuptools import setup, find_namespace_packages

requirements = [
    "numpy",
    "pandas",
    "vtkplotter>=2020.0.1",
    "vtk",
    "allensdk",
    "tqdm",
    "pyyaml>=5.3",
    "scikit-image",
    "brainio>=0.0.9",
]

setup(
    name="brainrender",
    version="0.3.3.7",
    description="Python scripts to use Allen Brain Map data for analysis "
                "and rendering",
    install_requires=requirements,
    extras_require={
        "nb": ["jupyter", "k3d"],
        "dev": [
            "pytest-cov",
            "pytest",
            "coveralls",
            "coverage<=4.5.4",
        ]
    },
    python_requires=">=3.6, <3.8",
    packages=find_namespace_packages(exclude=(
        "Installation", "Meshes", "Metadata", "Screenshots")),
    include_package_data=True,
    url="https://github.com/BrancoLab/brainrender",
    author="Federico Claudi",
    zip_safe=False,
)
