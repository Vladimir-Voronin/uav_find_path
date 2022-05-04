from abc import ABC


class IQgisResultVisualize(ABC):
    def visualize(self):
        raise NotImplementedError