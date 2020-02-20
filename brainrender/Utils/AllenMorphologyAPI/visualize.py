from brainrender.scene import Scene
from brainrender.Utils.parsers.mouselight import NeuronsParser
from brainrender.Utils.AllenMorphologyAPI.AllenMorphology import AllenMorphology


class AllenMorphologyVisualizer(Scene):
    def __init__(self):
        AllenMorphology.__init__(self)
        self.parser = NeuronsParser(Scene(), neurite_radius=1.5)

    def add_neurons(self, neurons, color=None):
        for neuron in neurons:
            actors, regions = self.parser.parse_neurons_swc_allen(neurons[0], 9999)

            for name, actor in actors.items():
                if actor is not None:
                    scene.add_vtkactor(actor)
            scene.render()
