from setuptools import setup, find_namespace_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

requirements = [
    "numpy",
    "pandas",
    "vedo>=2020.3.3",
    "k3d==2.7.4",
    "msgpack",
    "vtk<9.0.0",
    "allensdk",
    "pyyaml>=5.3",
    "scikit-image",
    "brainio>=0.0.19",
    "sklearn",
    "morphapi>=0.1.1.3",
    "requests",
    "rich",
    "bg-atlasapi>=0.0.7",
]

setup(
    name="brainrender",
    version="1.0.0.1rc2",
    description="Python scripts to use Allen Brain Map data for analysis "
    "and rendering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=requirements,
    extras_require={
        "nb": ["jupyter", "k3d"],
        "dev": [
            "pytest-cov",
            "pytest",
            "pytest-sugar",
            "coveralls",
            "coverage<=4.5.4",
            "pre-commit",
            "opencv-python",
            "jupyter",
        ],
    },
    python_requires=">=3.6, <3.8",
    packages=find_namespace_packages(
        exclude=("Installation", "Meshes", "Metadata", "Screenshots")
    ),
    include_package_data=True,
    url="https://github.com/BrancoLab/brainrender",
    author="Federico Claudi",
    zip_safe=False,
    entry_points={"console_scripts": ["brainrender = brainrender.cli:main"]},
)
