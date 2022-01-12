from qgis.core import *
from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy
from algorithms.abstract.SearchMethod import SearchMethodAbstract
from algorithms.addition.Visualizer import Visualizer
from algorithms.addition.QgsGraphSearcher import QgsGraphSearcher
from algorithms.addition.GeometryPointExpand import GeometryPointExpand
from algorithms.addition.RandomizeFunctions import RandomizeFunctions
from algorithms.addition.Decorators import measuretime
from algorithms.BaseAlgorithims.AlgorithmsBasedOnHallAndGrid import AlgoritmsBasedOnHallAndGrid
import math


class RandomizedRRTMethod(AlgoritmsBasedOnHallAndGrid, SearchMethodAbstract):
    def __init__(self, starting_point, target_point, obstacles, project):
        super().__init__(starting_point, target_point, obstacles, project)
        self.path_list = []

    @measuretime
    def __create_grid(self):
        super()._create_grid()

    @measuretime
    def __get_shorter_path(self, feats, increase_points=0):
        super()._get_shorter_path(feats, increase_points)

    @measuretime
    def __set_geometry_to_grid(self):
        super()._set_geometry_to_grid()

    def __get_new_point_to_path(self):
        pass

    # or left???
    def __is_right(self, a, b, c):
        return ((b.X - a.X) * (c.Y - a.Y) - (b.Y - a.Y) * (c.X - a.X)) > 0

    @measuretime
    def run(self):
        self.__set_geometry_to_grid()
        graph = None
        searcher = QgsGraphSearcher(graph, self.starting_point, self.target_point, 0)

        if not searcher.check_to_pave_the_way():
            print("the algorithm failed to pave the way")
            return None

        print("Length of min path is: ", searcher.min_length_to_vertex())

        # visualize the shortest tree graph
        feats = searcher.get_shortest_tree_features_list()
        Visualizer.update_layer_by_feats_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\short_tree.shp", feats)

        # search min path and visualize
        feats = searcher.get_features_from_min_path()
        Visualizer.update_layer_by_feats_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp", feats)

        self.__get_shorter_path(feats, 3)


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    proj = QgsProject.instance()
    proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
    point1 = QgsGeometry.fromPointXY(QgsPointXY(39.7899186, 47.2674382))
    point2 = QgsGeometry.fromPointXY(QgsPointXY(39.786187, 47.272900))
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"
    obstacles = QgsVectorLayer(path)
    check = RandomizedRoadmapGridMethod(point1, point2, obstacles, proj)
    check.run()
