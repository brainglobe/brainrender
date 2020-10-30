from setuptools import setup, find_namespace_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

requirements = [
    "numpy",
    "pandas",
    "vedo>=2020.4.1 ",
    "k3d==2.7.4",
    "msgpack",
    "pyyaml>=5.3",
    "morphapi>=0.1.2.4",
    "requests",
    "bg-atlasapi>=1.0.0",
    "tables",
    "pyinspect>=0.0.8",
    "qtpy",
    "napari",
]

setup(
    name="brainrender",
    version="2.0.0.0rc",
    description="Visualisation and exploration of brain atlases and other anatomical data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
    ],
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
            "allensdk",
        ],
        "pyside2": ["PySide2>=5.12.3"],
        "pyqt5": ["PyQt5>=5.12.3"],
    },
    python_requires=">=3.6",
    packages=find_namespace_packages(exclude=("tests, examples")),
    entry_points={
        "console_scripts": [
            "brainrender-gui = brainrender.gui.__init__:clilaunch",
        ]
    },
    include_package_data=True,
    url="https://github.com/brainglobe/brainrender",
    author="Federico Claudi, Adam Tyson, Luigi Petrucco",
    zip_safe=False,
)
