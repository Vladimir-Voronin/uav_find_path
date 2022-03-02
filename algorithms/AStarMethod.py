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
    def __init__(self, point, g, target_point, prev_node, coordinate_int_x, coordinate_int_y):
        self.point = point
        self.g = g
        x_full_difference = target_point.x() - point.x()
        y_full_difference = target_point.y() - point.y()
        self.h = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
        self.sum = self.g + self.h
        self.prev_node = prev_node
        self.coordinate_int_x = coordinate_int_x
        self.coordinate_int_y = coordinate_int_y


class AStarMethod(AlgoritmsBasedOnHallAndGrid, SearchAlgorithm, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 200
        super().__init__(findpathdata, debuglog, hall_width)
        self.point_search_distance = 3
        self.point_search_distance_diagonal = self.point_search_distance * math.sqrt(2)
        self.open_list = []
        self.closed_list = []

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
        x_full_difference = self.target_point.x() - node.point.x()
        y_full_difference = self.target_point.y() - node.point.y()
        return math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)

    def __add_new_neighbor(self, node):
        pass

    def __get_min_weight_node_in_open_list(self):
        pass

    def __start_searching(self):
        start_node = Node(self.starting_point, 0, self.target_point, None, 0, 0)
        self.open_list.append(start_node)
        while True:
            current_node = self.__get_min_weight_node_in_open_list()
            if self.__check_distance_to_target_point(current_node) < self.point_search_distance_diagonal:
                line = QgsGeometry.fromPolylineXY([current_node,
                                                   self.target_point])
                geometry = self.grid.get_multipolygon_by_points(source_point_expand, self.target_point_expand)
                if geometry.distance(line):
                    # END
                    break
            self.open_list.remove(current_node)
            self.closed_list.append(current_node)
            self.__add_new_neighbor(current_node)
        pass

    def run(self):
        debug_log.start_block("set geometry to the grid block")
        self._set_geometry_to_grid()
        debug_log.end_block("set geometry to the grid block")

        debug_log.start_block("start searching block")
        self.__start_searching()
        debug_log.end_block("start searching block")

    def visualise(self):
        pass


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    my_time = time.perf_counter()
    n = 1
    for i in range(n):
        proj = QgsProject.instance()
        proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
        point1 = QgsGeometry.fromPointXY(QgsPointXY(39.786790, 47.274523))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(39.785310, 47.269818))
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
