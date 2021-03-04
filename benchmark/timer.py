from rich.layout import Layout
from rich import print
from rich.panel import Panel
import time
import sys
import pyinspect as pi
from myterial import (
    salmon,
    orange,
    orange_darker,
    amber,
    pink_light,
    blue_light,
)
import multiprocessing
import os


def is_GPU_available():

    """
    Check NVIDIA with nvidia-smi command
    Returning code 0 if no error, it means NVIDIA is installed
    Other codes mean not installed
    """
    code = os.system("nvidia-smi")
    return code == 0


class SceneContent:
    def __init__(self, scene):
        self.scene = scene

    def __rich_console__(self, console, dimension):
        actors = pi.Report(
            "Scene actors", accent=salmon, dim=orange, color=orange
        )
        for act in self.scene.clean_actors:
            try:
                points = len(act.points())
            except AttributeError:
                points = 0
            actors.add(
                f"[bold][{amber}]- {act.name}[/bold][{orange_darker}] (type: [{orange}]{act.br_class}[/{orange}]) - [white dim]points: {points}"
            )
        yield Panel(actors.tb)


class Empty:
    def __rich_console__(self, *args):
        yield ""


class Timer:
    def __init__(self, scene, name=None):
        """
        Class to time how long it takes for a brainrender
        scene to render and print a nice summary of the results

        Arguments:
            scene: brainrender.Scene instance
        """
        self.name = name
        self.scene = scene

        # re add root to make sure it's included in timer
        scene.remove(scene.root)
        scene.add_brain_region("root", alpha=0.2)

    def __rich_console__(self, console, dimension):
        points = []
        for act in self.scene.clean_actors:
            try:
                points.append(len(act.points()))
            except AttributeError:
                pass
        tot_points = sum(points)

        yield ""
        yield ""
        if self.name is not None:
            yield f"        [b {orange}]{self.name}"

        yield ""
        yield f"     [bold {amber}]Scene info:"
        yield f"[{blue_light}]Total number of [b]actors[/b] in scene: [b {pink_light}]{len(self.scene.actors)}"
        yield f"[{blue_light}]Total number of [b]vertices[/b] in scene: [b {pink_light}]{tot_points}"

        yield ""
        yield f"     [bold {amber}]Duration and FPS:"

        t0 = self._pre_render_stop - self.start
        t1 = self.stop - self.start
        t_ratio = t0 / t1

        yield f"[{blue_light}]Scene preparation timer duration: [b {pink_light}]{t0:.2f} seconds"
        yield f"[{blue_light}]Total timer duration: [b {pink_light}]{t1:.2f} seconds"
        yield f"[{blue_light}]Fraction of time spent preparing scene: [b {pink_light}]{t_ratio:.2f}"
        yield f"[{blue_light}]Rendering [b]FPS[/b]: [b {pink_light}]{self.render_fps:.2f} frames per second"

        yield ""
        yield f"     [bold {amber}]System info:"
        yield f"[{blue_light}]Platform: [{pink_light}]{sys.platform}"
        yield f"[{blue_light}]Number of cores: [{pink_light}]{multiprocessing.cpu_count()}"
        yield f"[{blue_light}]GPU available: [{pink_light}]{is_GPU_available()}"

    def make_report(self):
        layout = Layout(direction="horizontal", height=20)
        layout.split(
            Layout(SceneContent(self.scene), name="scene", ratio=1),
            Layout(
                Empty(),
                ratio=0.2,
            ),
            Layout(self, name="summary", ratio=2),
        )
        print(layout)

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self._pre_render_stop = time.perf_counter()

        try:
            self.scene.render(interactive=False)
        except AttributeError:
            # it will fail when timing video creation
            pass

        self.stop = time.perf_counter()

        self.render_fps = (
            1 / self.scene.plotter.renderer.GetLastRenderTimeInSeconds()
        )
        self.make_report()


class SimpleTimer:
    def __init__(self, name):
        self.name = name

    def start(self):
        self.start = time.perf_counter()

    def stop(self, *args):
        stop = time.perf_counter()

        print(
            f"Timer [{pink_light}]{self.name}[/{pink_light}] terminated in [{pink_light}]{stop-self.start:.3f} seconds"
        )

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        stop = time.perf_counter()

        print(
            f"Timer [{pink_light}]{self.name}[/{pink_light}] terminated in [{pink_light}]{stop-self.start:.3f} seconds"
        )


if __name__ == "__main__":
    from brainrender import Scene

    scene = Scene(root=True, inset=False)

    with Timer(scene, name="Test timer") as timer:
        for br in ["TH", "MOs", "CA1"]:
            timer.scene.add_brain_region(br, silhouette=False)
