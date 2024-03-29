import time
from abc import ABC

from qgis.core import *
from qgis.analysis import QgsGraph, QgsNetworkDistanceStrategy

from algorithms.GdalUAV.transformation.coordinates.CoordinateTransform import CoordinateTransform
from ModuleInstruments.DebugLog import DebugLog
from algorithms.GdalUAV.processing.FindPathData import FindPathData
from algorithms.GdalUAV.processing.calculations.Graphs import GdalGraphSearcher
from algorithms.GdalUAV.exceptions.MethodsException import FailFindPathException, TimeToSucceedException
from algorithms.GdalUAV.Interfaces.SearchMethod import SearchMethodAbstract
from algorithms.GdalUAV.processing.Converter import ObjectsConverter
from algorithms.GdalUAV.qgis.visualization.Visualizer import Visualizer
from algorithms.GdalUAV.processing.GeometryPointExpand import GeometryPointExpand
from algorithms.GdalUAV.processing.calculations.RandomizeFunctions import RandomizeFunctions
from algorithms.GdalUAV.base.MethodBasedOnHallAndGrid import MethodBasedOnHallAndGrid
import math


class RandomizedRoadmapGridMethod(MethodBasedOnHallAndGrid, SearchMethodAbstract, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 150
        super().__init__(findpathdata, debuglog, hall_width)
        self.debuglog.info("Create new class")
        self.debuglog.info(f"There are {len(self.list_of_obstacles_geometry)} objects in list_of_obstacles_geometry")
        self.random_points_feats = None
        self.default_graph_feats = None
        self.min_short_path_tree_feats = None
        self.final_path = None

    def __create_grid(self):
        self.debuglog.start_block("create grid")
        super()._create_grid()
        self.debuglog.end_block("create grid")

    def __set_geometry_to_grid(self):
        self.debuglog.start_block("set geometry to grid")
        super()._set_geometry_to_grid()
        self.debuglog.end_block("set geometry to grid")

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
        self.random_points_feats = ObjectsConverter.list_of_geometry_points_to_feats(list_of_points)
        # endregion

        return list_of_points

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

        full_time = 0
        for id_1, point in enumerate(feats):
            time_current = time.perf_counter()

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

            full_time += time.perf_counter() - time_current
            if full_time > self.time_to_succeed:
                raise TimeToSucceedException("Search is out of time")

        for pares in list_to_duplicate_backwards:
            point1 = pares[0]
            point2 = pares[1]
            line = QgsGeometry.fromPolylineXY([qgs_graph.vertex(pares[1]).point(), qgs_graph.vertex(pares[0]).point()])
            list_of_lines.append(line)
            feat = QgsFeature()
            feat.setGeometry(line)
            qgs_graph.addEdge(point1, point2, [QgsNetworkDistanceStrategy().cost(line.length(), feat)])

        self.default_graph_feats = ObjectsConverter.list_of_geometry_to_feats(list_of_lines)
        print(self.debuglog.get_info())
        return qgs_graph

    def run(self):
        self.__set_geometry_to_grid()
        list_of_points = self.__get_points()
        graph = self.__create_graph(list_of_points)

        searcher = GdalGraphSearcher(graph, self.starting_point, self.target_point, 0)
        if not searcher.check_to_pave_the_way():
            raise FailFindPathException("Path wasn`t found")

        self.debuglog.info("Length of min path is: " + str(searcher.min_length_to_vertex()))
        print("Length of min path is: ", searcher.min_length_to_vertex())

        # get the shortest tree graph
        self.min_short_path_tree_feats = searcher.get_shortest_tree_features_list()

        self.debuglog.info("get_short_path_tree_feats")

        # get min path
        self.final_path = searcher.get_features_from_min_path()

        self.debuglog.info("get_pre_final_path")

        self.final_path = super()._get_shorter_path(self.final_path, 10, 60)

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
            Visualizer.update_layer_by_feats_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\check_line.shp",
                                                        self.default_graph_feats)
            Visualizer.update_layer_by_feats_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\short_tree.shp",
                                                          self.min_short_path_tree_feats)
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
        point1 = QgsGeometry.fromPointXY(QgsPointXY(4428210.45, 5955160.67))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(4428636.43, 5955381.07))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = CoordinateTransform.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      True,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = RandomizedRoadmapGridMethod(find_path_data, debug_log)
        my_time_full = 0
        check.run()
        check.visualize()
        print(debug_log.get_info())
    my_time = (time.perf_counter() - my_time) / n
    print(my_time)
