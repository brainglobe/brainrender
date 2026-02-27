from functools import partial, update_wrapper

import vedo
from myterial import orange_dark, salmon
from rich import print
from rich.syntax import Syntax

from brainrender import settings


class JupyterMixIn:  # pragma: no cover
    def __init__(self):  # pragma: no cover
        # keep track if we are in a jupyter notebook
        if vedo.settings.default_backend == "k3d":
            self.backend = "k3d"
        elif vedo.settings.default_backend == "itkwidgets":
            self.backend = "itkwidgets"
        else:
            self.backend = False

        # Can't use cartoon shader in a notebook
        if self.backend == "k3d" or self.backend == "itkwidgets":
            if settings.SHADER_STYLE == "cartoon":
                settings.SHADER_STYLE = "plastic"


class not_on_jupyter:  # pragma: no cover
    def __init__(self, func):  # pragma: no cover
        """
        A decorator to block some methods from
        running in jupyter notebooks
        """
        update_wrapper(self, func)
        self.func = func

    def __get__(self, obj, objtype):  # pragma: no cover
        """Support instance methods."""
        return partial(self.__call__, obj)

    def __call__(self, obj, *args, **kwargs):  # pragma: no cover
        backend = JupyterMixIn().backend
        if not backend:
            return self.func(obj, *args, **kwargs)
        else:
            print(
                f"[{orange_dark}]Cannot run function [bold {salmon}]{self.func.__name__}[/bold {salmon}] in a jupyter notebook.",
                f"[{orange_dark}]To use brainrender in a Jupyter notebook, set the vedo backend to 'k3d' before creating your scene:\n",
                Syntax("import vedo", lexer="python"),
                Syntax(
                    "vedo.settings.default_backend = 'k3d'", lexer="python"
                ),
                f"[{orange_dark}]Note: some features are not available in the k3d backend.",
                f"[{orange_dark}]To use all features, run brainrender in a standard Python script or interactive terminal instead.",
            )
            return None
