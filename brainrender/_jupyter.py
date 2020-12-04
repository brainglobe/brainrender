import vedo
from functools import update_wrapper, partial
from brainrender import settings


class JupyterMixIn:  # pragma: no cover
    def __init__(self):  # pragma: no cover
        # keep track if we are in a jupyter notebook
        if vedo.settings.notebookBackend == "k3d":
            self.backend = "k3d"
        elif vedo.settings.notebookBackend == "itkwidgets":
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
        if not backend or backend == "itkwidgets":
            return self.func(obj, *args, **kwargs)
        else:
            print(
                f"Cannot run function {self.func.__name__} in a jupyter notebook"
            )
            return None
