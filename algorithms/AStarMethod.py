import math
import time
from abc import ABC

from qgis.core import *
from algorithms.GdalUAV.transformation.coordinates.CoordinateTransform import CoordinateTransform
from ModuleInstruments.DebugLog import DebugLog
from algorithms.GdalUAV.processing.FindPathData import FindPathData
from algorithms.GdalUAV.base.MethodBasedOnHallOnly import MethodBasedOnHallOnly
from algorithms.GdalUAV.base.SearchMethodBase import SearchMethodBase
from algorithms.GdalUAV.exceptions.MethodsException import FailFindPathException, TimeToSucceedException
from algorithms.GdalUAV.processing.Converter import ObjectsConverter
from algorithms.GdalUAV.qgis.visualization.Visualizer import Visualizer


class Node:
    def __init__(self, point, g, target_point, prev_node, coordinate_int_x, coordinate_int_y, coef=1):
        self.point = point
        self.g = g
        x_full_difference = target_point.x() - point.x()
        y_full_difference = target_point.y() - point.y()
        self.h = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
        if prev_node is not None:
            self.diij_weight = prev_node.diij_weight + g
        else:
            self.diij_weight = g
        self.sum = self.diij_weight + coef * self.h
        self.prev_node = prev_node
        self.coordinate_int_x = coordinate_int_x
        self.coordinate_int_y = coordinate_int_y


class AStarMethod(MethodBasedOnHallOnly, SearchMethodBase, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 150
        super().__init__(findpathdata, debuglog, hall_width)

        self.point_search_distance = 2
        self.coef_heuristic = 1.2
        self.point_search_distance_diagonal = self.point_search_distance * math.sqrt(2)
        self.open_list = []
        self.closed_list = []
        self.all_nodes_list = []
        self.all_nodes_list_coor = []
        self.last_node = None

        self.list_of_path = []
        self.final_path = []
        self.is_succes = False

    def __check_distance_to_target_point(self, node):
        x_full_difference = self.target_point.x() - node.point.x()
        y_full_difference = self.target_point.y() - node.point.y()
        return math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)

    def __new_neighbor(self, node, x, y):
        new_x = node.coordinate_int_x + x
        new_y = node.coordinate_int_y + y

        if not [new_x, new_y] in self.all_nodes_list_coor:

            point = QgsPointXY(node.point.x() + x * self.point_search_distance,
                               node.point.y() + y * self.point_search_distance)
            point_geometry = QgsGeometry.fromPointXY(point)

            if self.hall.hall_polygon.distance(point_geometry) == 0 and (self.multi_polygon_geometry.distance(
                    point_geometry) > self.point_search_distance_diagonal) or self.multi_polygon_geometry.isNull():
                if point:
                    if (x == 1 or x == -1) and (y == 1 or y == -1):
                        new_node = Node(point, self.point_search_distance_diagonal, self.target_point,
                                        node, new_x, new_y, self.coef_heuristic)
                    else:
                        new_node = Node(point, self.point_search_distance, self.target_point, node,
                                        new_x, new_y, self.coef_heuristic)
                    self.open_list.append(new_node)
                    self.all_nodes_list.append(new_node)
                    self.all_nodes_list_coor.append([new_x, new_y])

    def __add_new_neighbors(self, node):
        self.__new_neighbor(node, 1, 0)
        self.__new_neighbor(node, 1, 1)
        self.__new_neighbor(node, 0, 1)
        self.__new_neighbor(node, -1, 1)
        self.__new_neighbor(node, -1, 0)
        self.__new_neighbor(node, -1, -1)
        self.__new_neighbor(node, 0, -1)
        self.__new_neighbor(node, 1, -1)

    def __get_min_weight_node_in_open_list(self):
        return min(self.open_list, key=lambda p: p.sum)

    def __find_path(self):
        node = self.last_node
        while node is not None:
            prev_node = node.prev_node
            if prev_node is not None:
                line = QgsGeometry.fromPolylineXY([node.prev_node.point,
                                                   node.point])
                self.list_of_path.append(line)
            node = node.prev_node
        self.list_of_path.reverse()

    def __start_searching(self):
        start_node = Node(self.starting_point, 0, self.target_point, None, 0, 0, self.coef_heuristic)
        self.open_list.append(start_node)
        self.all_nodes_list.append(start_node)
        self.all_nodes_list_coor.append([0, 0])

        full_time = 0
        while full_time < self.time_to_succeed:
            time_current = time.perf_counter()
            if not len(self.open_list):
                break
            current_node = self.__get_min_weight_node_in_open_list()

            if self.__check_distance_to_target_point(current_node) < self.point_search_distance_diagonal:
                line = QgsGeometry.fromPolylineXY([current_node.point,
                                                   self.target_point])

                if self.multi_polygon_geometry.distance(line):
                    self.last_node = Node(self.target_point, 0, self.target_point, current_node, 0, 0,
                                          self.coef_heuristic)
                    self.is_succes = True
                    break
            self.open_list.remove(current_node)
            self.closed_list.append(current_node)

            self.__add_new_neighbors(current_node)

            full_time += time.perf_counter() - time_current
        else:
            raise TimeToSucceedException("Search is out of time")

        if not self.is_succes:
            raise FailFindPathException("Path wasn`t found")

    def run(self):
        self.debuglog.start_block("start searching block")
        self.__start_searching()
        self.debuglog.end_block("start searching block")

        self.debuglog.start_block("find path block")
        self.__find_path()
        self.debuglog.end_block("find path block")

        self.final_path = self._get_shorter_path(self.list_of_path)

    def visualize(self):
        if self.create_debug_layers:
            points_feats = ObjectsConverter.list_of_geometry_to_feats(self.all_nodes_list)
            min_short_feats = ObjectsConverter.list_of_geometry_to_feats(self.list_of_path)
            Visualizer.create_and_add_new_default_points(self.project, self.path_to_save_layers,
                                                         points_feats)
            Visualizer.create_and_add_new_path_short_tree(self.project, self.path_to_save_layers,
                                                          min_short_feats)
        Visualizer.create_and_add_new_final_path(self.project, self.path_to_save_layers, self.final_path)
        if __name__ == '__main__':
            points_geom = [QgsGeometry.fromPointXY(x.point) for x in self.all_nodes_list]
            Visualizer.update_layer_by_geometry_objects(
                r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp", points_geom)
            Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp",
                                                        self.list_of_path)
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
        point1 = QgsGeometry.fromPointXY(QgsPointXY(4428288.22, 5955188.73))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(4428577.28, 5955405.37))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = CoordinateTransform.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      False,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = AStarMethod(find_path_data, debug_log)
        check.run()
        check.visualize()
        print(debug_log.get_info())

    my_time = (time.perf_counter() - my_time) / n
    print(my_time)
