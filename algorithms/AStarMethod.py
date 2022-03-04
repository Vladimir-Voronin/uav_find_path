import math
import random
import time
from abc import ABC

from qgis.core import *
from ModuleInstruments.Converter import Converter
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
from algorithms.BaseAlgorithims.AlgorithmsBasedOnHallAndGrid import AlgoritmsBasedOnHallAndGrid
from algorithms.BaseAlgorithims.SearchAlgorthim import SearchAlgorithm
from algorithms.addition.GdalExtentions import ObjectsConverter
from algorithms.addition.GeometryPointExpand import GeometryPointExpand
from algorithms.addition.Visualizer import Visualizer


class Node:
    def __init__(self, point_expand, g, target_point, prev_node, coordinate_int_x, coordinate_int_y):
        self.point_expand = point_expand
        self.g = g
        x_full_difference = target_point.x() - point_expand.point.x()
        y_full_difference = target_point.y() - point_expand.point.y()
        self.h = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
        self.sum = self.g + self.h
        self.prev_node = prev_node
        self.coordinate_int_x = coordinate_int_x
        self.coordinate_int_y = coordinate_int_y


class AStarMethod(AlgoritmsBasedOnHallAndGrid, SearchAlgorithm, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 200
        super().__init__(findpathdata, debuglog, hall_width)

        cell_target = self.grid.difine_point(self.target_point_geometry)
        self.target_point_expand = GeometryPointExpand(self.target_point, cell_target.n_row,
                                                       cell_target.n_column)

        self.point_search_distance = 2
        self.point_search_distance_diagonal = self.point_search_distance * math.sqrt(2)
        self.open_list = []
        self.closed_list = []
        self.all_nodes_list = []
        self.last_node = None

        self.list_of_path = []
        self.final_path = []
        self.is_succes = False

    def __create_grid(self):
        self.debuglog.start_block("create grid")
        super()._create_grid()
        self.debuglog.end_block("create grid")

    def __get_shorter_path(self, feats, increase_points=0):
        self.debuglog.start_block("get shorter path")
        result = super()._get_shorter_path(feats, increase_points)
        self.debuglog.end_block("get shorter path")
        return result

    def __set_geometry_to_grid(self):
        self.debuglog.start_block("set geometry to grid")
        super()._set_geometry_to_grid()
        self.debuglog.end_block("set geometry to grid")

    def __check_distance_to_target_point(self, node):
        x_full_difference = self.target_point.x() - node.point_expand.point.x()
        y_full_difference = self.target_point.y() - node.point_expand.point.y()
        return math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)

    def __new_neighbor(self, node, x, y):
        new_x = node.coordinate_int_x + x
        new_y = node.coordinate_int_y + y

        match = filter(lambda node_: node_.coordinate_int_x == new_x and node_.coordinate_int_y == new_y,
                       self.all_nodes_list)
        first = next(match, None)

        if not first:

            point = QgsPointXY(node.point_expand.point.x() + x * self.point_search_distance,
                               node.point_expand.point.y() + y * self.point_search_distance)
            point_geometry = QgsGeometry.fromPointXY(point)

            cell = self.grid.define_point_using_math_search(point)
            if cell is not None:
                if self.hall.hall_polygon.distance(point_geometry) == 0 and (cell.geometry.distance(
                        point_geometry) > self.point_search_distance_diagonal) or cell.geometry.isNull():
                    point_expand = self.grid.get_point_expand_by_point(point)
                    if (x == 1 or x == -1) and (y == 1 or y == -1):
                        new_node = Node(point_expand, self.point_search_distance_diagonal, self.target_point,
                                        node,
                                        node.coordinate_int_x + x, node.coordinate_int_y + y)
                    else:
                        new_node = Node(point_expand, self.point_search_distance, self.target_point, node,
                                        node.coordinate_int_x + x, node.coordinate_int_y + y)
                    self.open_list.append(new_node)
                    self.all_nodes_list.append(new_node)

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
                line = QgsGeometry.fromPolylineXY([node.prev_node.point_expand.point,
                                                   node.point_expand.point])
                self.list_of_path.append(line)
            node = node.prev_node
        self.list_of_path.reverse()

    def __start_searching(self):
        start_point_expand = self.grid.get_point_expand_by_point(self.starting_point)
        start_node = Node(start_point_expand, 0, self.target_point, None, 0, 0)
        self.open_list.append(start_node)
        self.all_nodes_list.append(start_node)
        while True:
            if not len(self.open_list):
                raise Exception("Path wasn`t found")
            current_node = self.__get_min_weight_node_in_open_list()

            if self.__check_distance_to_target_point(current_node) < self.point_search_distance_diagonal:
                line = QgsGeometry.fromPolylineXY([current_node.point_expand.point,
                                                   self.target_point])
                geometry = self.grid.get_multipolygon_by_points(current_node.point_expand, self.target_point_expand)
                if geometry.distance(line):
                    self.last_node = Node(self.target_point_expand, 0, self.target_point, current_node, 0, 0)
                    self.is_succes = True
                    break
            self.open_list.remove(current_node)
            self.closed_list.append(current_node)

            self.__add_new_neighbors(current_node)

    def run(self):
        debug_log.start_block("set geometry to the grid block")
        self._set_geometry_to_grid()
        debug_log.end_block("set geometry to the grid block")

        debug_log.start_block("start searching block")
        self.__start_searching()
        debug_log.end_block("start searching block")

        debug_log.start_block("find path block")
        self.__find_path()
        debug_log.end_block("find path block")

        self.final_path = self.__get_shorter_path(self.list_of_path)
        self.visualise()

    def visualise(self):
        if self.create_debug_layers:
            points_feats = ObjectsConverter.list_of_geometry_to_feats(self.all_nodes_list)
            min_short_feats = ObjectsConverter.list_of_geometry_to_feats(self.list_of_path)
            Visualizer.create_and_add_new_default_points(self.project, self.path_to_save_layers,
                                                         points_feats)
            Visualizer.create_and_add_new_path_short_tree(self.project, self.path_to_save_layers,
                                                          min_short_feats)
        Visualizer.create_and_add_new_final_path(self.project, self.path_to_save_layers, self.final_path)
        if __name__ == '__main__':
            points_geom = [QgsGeometry.fromPointXY(x.point_expand.point) for x in self.all_nodes_list]
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
        point1 = QgsGeometry.fromPointXY(QgsPointXY(39.7867695,47.2744990))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(39.7794512, 47.2741065))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      False,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = AStarMethod(find_path_data, debug_log)
        check.run()
        print(debug_log.get_info())
    my_time = (time.perf_counter() - my_time) / n
    print(my_time)
