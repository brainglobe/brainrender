from setuptools import setup, find_packages
from os import path
from pathlib import Path
import codecs

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


def read(path):
    with codecs.open(path, "r") as fp:
        return fp.read()


def get_version():
    path = Path(this_directory) / "brainrender" / "__init__.py"

    for line in read(path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


requirements = [
    "numpy",
    "pandas",
    "vedo>=2021.0.3",
    "k3d==2.7.4",
    "msgpack",
    "pyyaml>=5.3",
    "morphapi>=0.1.3.0",
    "requests",
    "bg-atlasapi>=1.0.0",
    "tables",
    "pyinspect>=0.0.8",
    "qtpy",
    "myterial",
    "loguru",
]

setup(
    name="brainrender",
    version=get_version(),
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
        "lint": [
            "black",
            "flake8",
        ],
        "nb": ["jupyter", "k3d"],
        "dev": [
            "pytest-cov",
            "pytest-qt",
            "pytest",
            "pytest-sugar",
            "coveralls",
            "coverage<=4.5.4",
            "black",
            "flake8",
            "pre-commit",
            "opencv-python",
            "jupyter",
            "allensdk",
            "PySide2>=5.12.3",
            "k3d",
            "imio",
        ],
        "pyside2": ["PySide2>=5.12.3"],
        "pyqt5": ["PyQt5>=5.12.3"],
    },
    python_requires=">=3.6",
    packages=find_packages(
        include=("brianrender", "brainrender.*"),
        exclude=(
            "tests",
            "examples",
            "benchmark",
            ".paper",
            "imgs",
            "videos",
            "tests.*",
            "examples.*",
            "benchmark.*",
            ".paper.*",
            "imgs.*",
            "videos.*",
        ),
    ),
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
