import random

from memory_profiler import memory_usage, profile
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


class RandomizedRoadmapGridMethod(AlgoritmsBasedOnHallAndGrid, SearchMethodAbstract):
    def __init__(self, starting_point, target_point, obstacles, project):
        super().__init__(starting_point, target_point, obstacles, project)

    @measuretime
    def __create_grid(self):
        super()._create_grid()

    @measuretime
    def __get_shorter_path(self, feats, increase_points=0):
        super()._get_shorter_path(feats, increase_points)

    @measuretime
    def __set_geometry_to_grid(self):
        super()._set_geometry_to_grid()

    @measuretime
    def __get_points(self):
        # 1 point for "self.const_square_meters" square meters
        amount_of_points = math.ceil(self.hall.square / self.const_square_meters)

        list_of_points = RandomizeFunctions.get_random_extended_points(self.hall, amount_of_points, self.grid)

        # adding starting and target points + points around of them
        list_points_around_starting = RandomizeFunctions.get_extended_points_around(self.starting_point, 20, self.grid)
        list_points_around_target = RandomizeFunctions.get_extended_points_around(self.target_point, 20, self.grid)

        list_of_points.extend(list_points_around_starting)
        list_of_points.extend(list_points_around_target)
        cell_start = self.grid.difine_point(self.starting_point_geometry)
        start_point_expand = GeometryPointExpand(self.starting_point_geometry, cell_start.n_row, cell_start.n_column)
        cell_target = self.grid.difine_point(self.target_point_geometry)
        target_point_expand = GeometryPointExpand(self.target_point_geometry, cell_target.n_row, cell_target.n_column)

        list_of_points.append(start_point_expand)
        list_of_points.append(target_point_expand)

        # region display points, may delete
        Visualizer.update_layer_by_extended_points(
            r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp",
            list_of_points, True)
        # endregion

        return list_of_points

    @measuretime
    def __create_graph(self, list_of_points):
        feats = GeometryPointExpand.transform_to_list_of_feats(list_of_points)

        qgs_graph = QgsGraph()
        for point in list_of_points:
            qgs_graph.addVertex(point.point.asPoint())
        index = QgsSpatialIndex()
        index.addFeatures(feats)

        # list to except double edges
        list_of_excepts = []
        # list to dublicate backwards
        list_to_duplicate_backwards = []
        # list_of_lines contain type QgsGeometry
        list_of_lines = []

        for id_1, point in enumerate(feats):
            nearest = index.nearestNeighbor(point.geometry().asPoint(), self.const_sight_of_points)
            nearest.pop(0)
            # iterates over nearest points, try to create line
            for nearest_point_id in nearest:
                if [id_1, nearest_point_id] not in list_of_excepts:
                    # add to list of excepts
                    list_of_excepts.append([id_1, nearest_point_id])

                    line = QgsGeometry.fromPolylineXY([point.geometry().asPoint(),
                                                       feats[nearest_point_id].geometry().asPoint()])

                    geometry = self.grid.get_multipolygon_by_points(list_of_points[id_1],
                                                                    list_of_points[nearest_point_id])

                    if geometry.distance(line):
                        # add to list of duplicates backwards, ADDING IS BACKWARD
                        list_to_duplicate_backwards.append([nearest_point_id, id_1])
                        # # add to list_of_lines # QgsGeometry
                        list_of_lines.append(line)
                        feat = QgsFeature()
                        feat.setGeometry(line)
                        qgs_graph.addEdge(id_1, nearest_point_id,
                                          [QgsNetworkDistanceStrategy().cost(line.length(), feat)])

        for pares in list_to_duplicate_backwards:
            point1 = pares[0]
            point2 = pares[1]
            line = QgsGeometry.fromPolylineXY([qgs_graph.vertex(pares[1]).point(), qgs_graph.vertex(pares[0]).point()])
            list_of_lines.append(line)
            feat = QgsFeature()
            feat.setGeometry(line)
            qgs_graph.addEdge(point1, point2, [QgsNetworkDistanceStrategy().cost(line.length(), feat)])

        Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\check_line.shp",
                                                    list_of_lines)

        return qgs_graph

    @measuretime
    def run(self):
        self.__set_geometry_to_grid()
        list_of_points = self.__get_points()
        graph = self.__create_graph(list_of_points)
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
    point1 = QgsGeometry.fromPointXY(QgsPointXY(39.7897843,47.2679031))
    point2 = QgsGeometry.fromPointXY(QgsPointXY(39.7848538,47.2733796))
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"
    obstacles = QgsVectorLayer(path)
    check = RandomizedRoadmapGridMethod(point1, point2, obstacles, proj)
    check.run()
