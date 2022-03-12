from abc import ABC


class DynamicAlgorithm(ABC):
    def update(self, list_of_geometry_obstacles):
        raise NotImplementedError

    def get_updated_path(self):
        raise NotImplementedError
