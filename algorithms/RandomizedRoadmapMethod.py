from abc import ABC

from qgis.core import *
from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy

from ModuleInstruments.Converter import Converter
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
from algorithms.BaseAlgorithims.AlgorithmsBasedOnHallAndGrid import AlgoritmsBasedOnHallAndGrid
from algorithms.BaseAlgorithims.AlgorithmsBasedOnHallOnly import AlgorithmsBasedOnHallOnly
from algorithms.GdalFPExtension.calculations.Graphs import GdalGraphSearcher
from algorithms.GdalFPExtension.exceptions.MethodsException import TimeToSucceedException, FailFindPathException
from algorithms.GdalFPExtension.gdalObjects.Converter import ObjectsConverter
from algorithms.GdalFPExtension.methodsInterfaces.SearchMethod import SearchMethodAbstract
from algorithms.addition.Decorators import measuretime
from algorithms.GdalFPExtension.qgis.visualization.Visualizer import Visualizer
from algorithms.GdalFPExtension.grid.Hall import Hall
from algorithms.GdalFPExtension.gdalObjects.RandomizeFunctions import RandomizeFunctions
from algorithms.BaseAlgorithims.SearchAlgorthim import SearchAlgorithm
import math
import time
import sys

sys.path.insert(0, r'C:\OSGeo4W64\apps\Python37\lib')


class RandomizedRoadmapMethod(AlgorithmsBasedOnHallOnly, SearchAlgorithm, SearchMethodAbstract, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 150
        super().__init__(findpathdata, debuglog, hall_width)

        # constants
        self.const_square_meters = 400
        self.const_sight_of_points = 12

        self.min_short_path_tree_feats = []
        self.random_points_feats = []
        self.default_graph_feats = []
        self.pre_final_path = []
        self.final_path = []

    @measuretime
    def __create_graph(self):
        # 1 point for "self.const_square_meters" square meters
        amount_of_points = math.ceil(self.hall.square / self.const_square_meters)

        list_of_points = RandomizeFunctions.get_random_points(self.hall, amount_of_points, self.multi_polygon_geometry)

        # adding starting and target points + points around of them
        list_points_around_starting = RandomizeFunctions.get_points_around(self.starting_point,
                                                                           20,
                                                                           self.multi_polygon_geometry)
        list_points_around_target = RandomizeFunctions.get_points_around(self.target_point,
                                                                         20,
                                                                         self.multi_polygon_geometry)

        list_of_points.extend(list_points_around_starting)
        list_of_points.extend(list_points_around_target)
        list_of_points.append(self.starting_point_geometry)
        list_of_points.append(self.target_point_geometry)

        # region display points, may delete
        vlayer1 = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp")
        vlayer1.dataProvider().truncate()

        feats = []
        id_number = -1
        for point in list_of_points:
            id_number += 1
            feat = QgsFeature(vlayer1.fields())
            feat.setId(id_number)
            feat.setGeometry(point)
            feats.append(feat)
        vlayer1.dataProvider().addFeatures(feats)
        # endregion
        print("ST1")
        self.random_points_feats = feats

        # creating graph
        qgs_graph = QgsGraph()
        for point in list_of_points:
            qgs_graph.addVertex(point.asPoint())
        index = QgsSpatialIndex()
        index.addFeatures(feats)

        vlayer2 = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\check_line.shp")
        vlayer2.dataProvider().truncate()
        # list to except double edges
        list_of_excepts = []
        # list to dublicate backwords
        list_to_duplicate_backwords = []
        # list_of_lines contain type QgsGeometry
        list_of_lines = []
        # feats_line contain type QgsFeature
        feats_line = []
        id_number = -1

        full_time = 0
        for point in feats:
            time_current = time.perf_counter()

            nearest = index.nearestNeighbor(point.geometry().asPoint(), self.const_sight_of_points)
            nearest.pop(0)

            # iterates over nearest points, try to create line
            for nearest_point_id in nearest:

                point1 = qgs_graph.findVertex(point.geometry().asPoint())
                point2 = qgs_graph.findVertex(feats[nearest_point_id].geometry().asPoint())
                if sorted([point1, point2]) not in list_of_excepts:
                    # add to list of excepts
                    list_of_excepts.append([point1, point2])
                    line = QgsGeometry.fromPolylineXY([point.geometry().asPoint(),
                                                       feats[nearest_point_id].geometry().asPoint()])

                    if self.multi_polygon_geometry.distance(line) > 0.0:
                        # add to list of duplicates backwords, ADDING IS BACKWORD
                        list_to_duplicate_backwords.append([point2, point1])
                        # add to list_of_lines # QgsGeometry
                        list_of_lines.append(line)
                        id_number += 1
                        # Create QgsFeature and add to feats_line
                        feat = QgsFeature(vlayer2.fields())
                        feat.setId(id_number)
                        feat.setGeometry(line)
                        feats_line.append(feat)
                        qgs_graph.addEdge(point1, point2, [QgsNetworkDistanceStrategy().cost(line.length(), feat)])

            full_time += time.perf_counter() - time_current
            if full_time > self.time_to_succeed:
                raise TimeToSucceedException("Search is out of time")

        # duplicate edge backwords
        for pares in list_to_duplicate_backwords:
            point1 = pares[0]
            point2 = pares[1]
            line = QgsGeometry.fromPolylineXY([qgs_graph.vertex(pares[1]).point(), qgs_graph.vertex(pares[0]).point()])
            list_of_lines.append(line)
            id_number += 1
            # Create QgsFeature and add to feats_line
            feat = QgsFeature(vlayer2.fields())
            feat.setId(id_number)
            feat.setGeometry(line)
            feats_line.append(feat)
            qgs_graph.addEdge(point1, point2, [QgsNetworkDistanceStrategy().cost(line.length(), feat)])

        vlayer2.dataProvider().addFeatures(feats_line)
        self.default_graph_feats = feats_line
        return qgs_graph

    def run(self):
        graph = self.__create_graph()
        searcher = GdalGraphSearcher(graph, self.starting_point, self.target_point, 0)

        if not searcher.check_to_pave_the_way():
            raise FailFindPathException("Path wasn`t found")

        # get the shortest tree graph
        self.min_short_path_tree_feats = searcher.get_shortest_tree_features_list()

        self.debuglog.info("get_short_path_tree_feats")

        # get min path
        self.pre_final_path = searcher.get_features_from_min_path()

        self.debuglog.info("get_pre_final_path")

        self.final_path = self._get_shorter_path(self.pre_final_path, 2)

        self.debuglog.info("get_final_path")

    def visualize(self):
        if self.create_debug_layers:
            Visualizer.create_and_add_new_default_points(self.project, self.path_to_save_layers,
                                                         self.random_points_feats)
            Visualizer.create_and_add_new_default_graph(self.project, self.path_to_save_layers,
                                                        self.default_graph_feats)
            Visualizer.create_and_add_new_path_short_tree(self.project, self.path_to_save_layers,
                                                          self.min_short_path_tree_feats)
        Visualizer.create_and_add_new_final_path(self.project, self.path_to_save_layers, self.final_path)

        if __name__ == '__main__':
            Visualizer.update_layer_by_feats_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp",
                                                     self.random_points_feats)
            Visualizer.update_layer_by_feats_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp",
                                                     self.pre_final_path)
            Visualizer.update_layer_by_feats_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\short_path.shp",
                                                     self.final_path)


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    my_time = time.perf_counter()
    n = 1
    for i in range(n):
        proj = QgsProject.instance()
        proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
        point1 = QgsGeometry.fromPointXY(QgsPointXY(4428094.059841852, 5955751.246513667))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(4428670.438183919, 5957666.393507188))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      False,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = RandomizedRoadmapMethod(find_path_data, debug_log)
        my_time_full = 0
        check.run()
        check.visualize()
        print(debug_log.get_info())
    my_time = (time.perf_counter() - my_time) / n
    print(my_time)
