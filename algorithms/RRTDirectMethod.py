import math
import random
import time
from abc import ABC

from memory_profiler import profile, memory_usage
from qgis.core import *
from ModuleInstruments.Converter import Converter
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
from algorithms.BaseAlgorithims.AlgorithmsBasedOnHallAndGrid import AlgoritmsBasedOnHallAndGrid
from algorithms.BaseAlgorithims.SearchAlgorthim import SearchAlgorithm
from algorithms.GdalFPExtension.gdalObjects.Converter import ObjectsConverter
from algorithms.GdalFPExtension.gdalObjects.GeometryPointExpand import GeometryPointExpand
from algorithms.GdalFPExtension.qgis.visualization.Visualizer import Visualizer


class TreeNode:
    def __init__(self, point_expand, prev_node, prev_line):
        self.point_expand = point_expand
        self.prev_line = prev_line
        self.prev_node = prev_node
        self.distance_to_target = None


class RRTDirectMethod(AlgoritmsBasedOnHallAndGrid, SearchAlgorithm, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 200
        super().__init__(findpathdata, debuglog, hall_width)
        self.max_search_distance = 40

        cell_start = self.grid.difine_point(self.starting_point_geometry)
        self.start_point_expand = GeometryPointExpand(self.starting_point_geometry, cell_start.n_row,
                                                      cell_start.n_column)
        cell_target = self.grid.difine_point(self.target_point_geometry)
        self.target_point_expand = GeometryPointExpand(self.target_point_geometry, cell_target.n_row,
                                                       cell_target.n_column)

        self.point_analysis_list = []
        self.list_of_treenodes = []
        self.max_active_nodes_in_list = 25
        self.attempts_to_each_node = 3
        self.tree_reached_target = False
        self.last_node = None
        self.list_of_path = []
        self.final_path = []

        # debug
        self.time_of_work_starts = time.perf_counter()
        self.time_stop = 30  # seconds to drop the algorithm

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

    def __find_path_in_tree(self):
        node = self.last_node
        while node is not None:
            if node.prev_line is not None:
                self.list_of_path.append(node.prev_line)
            node = node.prev_node

    def __get_point_ahead(self, source_point_node):
        source_point_expand = source_point_node.point_expand
        source_point = source_point_expand.point.asPoint()
        target_point = self.target_point_expand.point.asPoint()
        x_full_difference = target_point.x() - source_point.x()
        y_full_difference = target_point.y() - source_point.y()
        distance_to_target_point = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)

        if distance_to_target_point < self.max_search_distance:
            line = QgsGeometry.fromPolylineXY([source_point,
                                               target_point])
            geometry = self.grid.get_multipolygon_by_points(source_point_expand, self.target_point_expand)
            if geometry.distance(line):
                # Add logic
                self.tree_reached_target = True
                node = TreeNode(self.target_point_expand, source_point_node, line)
                node.distance_to_target = distance_to_target_point
                self.last_node = node
                return None

        x_unit = x_full_difference / distance_to_target_point
        y_unit = y_full_difference / distance_to_target_point
        angle = random.randint(-90, 90)
        rad = math.radians(angle)
        length = random.randint(1, self.max_search_distance)

        x_increment = x_unit * length
        y_increment = y_unit * length
        new_point_coordinates_x = source_point.x() + x_increment
        new_point_coordinates_y = source_point.y() + y_increment

        Xp = (new_point_coordinates_x - source_point.x()) * math.cos(rad) - (
                new_point_coordinates_y - source_point.y()) * math.sin(rad)
        Yp = (new_point_coordinates_x - source_point.x()) * math.sin(rad) + (
                new_point_coordinates_y - source_point.y()) * math.cos(rad)

        new_point = QgsGeometry.fromPointXY(
            QgsPointXY(source_point.x() + Xp, source_point.y() + Yp))

        cell_for_new_point = self.grid.difine_point(new_point)
        if cell_for_new_point is None:
            return None

        new_point_expand = GeometryPointExpand(new_point, cell_for_new_point.n_row,
                                               cell_for_new_point.n_column)

        geometry = self.grid.get_multipolygon_by_points(source_point_expand, new_point_expand)
        if geometry is None:
            return None

        # Perhaps it will be faster if we skip this check (check for a line at once)
        if self.hall.hall_polygon.distance(new_point) == 0 and geometry.distance(new_point):
            line = QgsGeometry.fromPolylineXY([source_point,
                                               new_point.asPoint()])
            if geometry.distance(line):
                node = TreeNode(new_point_expand, source_point_node, line)
                node.distance_to_target = distance_to_target_point
                self.list_of_treenodes.append(node)

    def __one_step_of_the_loop(self):
        copy_list = self.point_analysis_list.copy()
        for node in copy_list:
            for i in range(self.attempts_to_each_node):
                self.__get_point_ahead(node)
                if self.tree_reached_target:
                    break

    def __handle_list_of_nodes(self):
        if len(self.list_of_treenodes) > self.max_active_nodes_in_list:
            self.list_of_treenodes.sort(key=lambda x: x.distance_to_target)
            self.point_analysis_list = self.list_of_treenodes[0:self.max_active_nodes_in_list]

    def __start_searching(self):
        start_point_node = TreeNode(self.start_point_expand, None, None)

        source_point = self.start_point_expand.point.asPoint()
        target_point = self.target_point_expand.point.asPoint()
        x_full_difference = target_point.x() - source_point.x()
        y_full_difference = target_point.y() - source_point.y()
        distance_between_points = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
        start_point_node.distance_to_target = distance_between_points

        self.list_of_treenodes.append(start_point_node)
        self.point_analysis_list.append(start_point_node)

        is_ok = False
        while time.perf_counter() - self.time_of_work_starts < self.time_stop:
            self.__handle_list_of_nodes()
            self.__one_step_of_the_loop()
            if self.tree_reached_target:
                is_ok = True
                break
        if not is_ok:
            raise QgsException("RRTDirectMethod failed to search result")

    def run(self):
        self.debuglog.start_block("set geometry to the grid block")
        self._set_geometry_to_grid()
        self.debuglog.end_block("set geometry to the grid block")

        self.debuglog.start_block("start searching block")
        self.__start_searching()
        self.debuglog.end_block("start searching block")

        self.debuglog.start_block("find pre min path")
        self.__find_path_in_tree()
        self.debuglog.end_block("find pre min path")
        self.debuglog.start_block("get final path")

        path_feats = ObjectsConverter.list_of_geometry_to_feats(self.list_of_path)
        path_feats.reverse()
        self.final_path = self.__get_shorter_path(path_feats, 3)
        self.debuglog.end_block("get final path")

    def get_pre_list_of_path(self):
        return self.list_of_path

    def get_final_list_of_path(self):
        return self.final_path

    def visualize(self):
        tree_to_visualize = [x.prev_line for x in self.list_of_treenodes]
        if self.create_debug_layers:
            min_short_feats = ObjectsConverter.list_of_geometry_to_feats(tree_to_visualize)
            Visualizer.create_and_add_new_path_short_tree(self.project, self.path_to_save_layers,
                                                          min_short_feats)
        Visualizer.create_and_add_new_final_path(self.project, self.path_to_save_layers, self.final_path)
        if __name__ == '__main__':
            Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\short_tree.shp",
                                                        tree_to_visualize)

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
        point1 = QgsGeometry.fromPointXY(QgsPointXY(4426633.9, 5957487.3))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(4426401.5, 5957303.1))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      False,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = RRTDirectMethod(find_path_data, debug_log)
        check.run()
        check.visualize()
        print(debug_log.get_info())
    my_time = (time.perf_counter() - my_time) / n
    print(my_time)
