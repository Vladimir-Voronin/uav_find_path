from abc import ABC
from checks.check_abstract import SearchMethod


class DynamicAlgorithm(ABC):
    def update(self, list_of_geometry_obstacles):
        raise NotImplementedError

    def get_updated_path(self):
        raise NotImplementedError
