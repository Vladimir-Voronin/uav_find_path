import math
import numpy as np
import time
from abc import ABC

from qgis.core import *
from algorithms.GdalUAV.transformation.coordinates.CoordinateTransform import CoordinateTransform
from ModuleInstruments.DebugLog import DebugLog
from algorithms.GdalUAV.processing.FindPathData import FindPathData
from algorithms.GdalUAV.base.MethodBasedOnHallAndGrid import MethodBasedOnHallAndGrid
from algorithms.GdalUAV.base.SearchMethodBase import SearchMethodBase
from algorithms.GdalUAV.exceptions.MethodsException import FailFindPathException, TimeToSucceedException
from algorithms.GdalUAV.processing.Converter import ObjectsConverter
from algorithms.GdalUAV.processing.GeometryPointExpand import GeometryPointExpand
from algorithms.GdalUAV.qgis.visualization.Visualizer import Visualizer


class NodeAPF:
    def __init__(self, point_expand, coordinate_int_x, coordinate_int_y):
        self.point_expand = point_expand
        self.coordinate_int_x = coordinate_int_x
        self.coordinate_int_y = coordinate_int_y
        self.target_vector_x = None
        self.target_vector_y = None
        self.obstacle_vector_x = None
        self.obstacle_vector_y = None
        self.sum_vector_x = None
        self.sum_vector_y = None
        self.min_dist_obstacle = None
        self.near_to_target = None

    def calculate_sum(self):
        if self.obstacle_vector_x is not None and self.obstacle_vector_y is not None:
            self.sum_vector_x = self.target_vector_x + self.obstacle_vector_x
            self.sum_vector_y = self.target_vector_y + self.obstacle_vector_y
        else:
            self.sum_vector_x = self.target_vector_x
            self.sum_vector_y = self.target_vector_y


class ObstacleAPF:
    def __init__(self, obstacle_geometry):
        self.obstacle_geometry = obstacle_geometry
        self.centroid = obstacle_geometry.centroid().asPoint()


class LinkedAngle:
    def __init__(self, angle):
        self.angle = angle
        self.prev = None
        self.next = None
        self.add_x = None
        self.add_y = None


class APFMethodOptimize(MethodBasedOnHallAndGrid, SearchMethodBase, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 100
        super().__init__(findpathdata, debuglog, hall_width)

        cell_target = self.grid.difine_point(self.target_point_geometry)
        self.target_point_expand = GeometryPointExpand(self.target_point, cell_target.n_row,
                                                       cell_target.n_column)

        self.point_search_distance = 2
        self.point_search_distance_diagonal = self.point_search_distance * math.sqrt(2)

        self.length_from_obstacle_to_analysis = 10
        self.powerful_of_vector_to_target = 2
        self.powerful_of_vector_from_obstacle = 2

        self.path_list_points = []
        self.all_nodes_list = []
        self.all_nodes_list_coor = []
        self.list_of_obstacles_apf = []

        self.linked_angle_current = None

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

    def __create_linked_angle(self):
        search_range = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
        coeficients = [[1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1], [0, 1]]
        linked_list = []
        for i in range(len(search_range)):
            current = LinkedAngle(search_range[i])
            current.add_x = coeficients[i][0]
            current.add_y = coeficients[i][1]
            linked_list.append(current)

        for i in range(len(linked_list)):
            if i + 1 != len(linked_list):
                linked_list[i].next = linked_list[i + 1]
            else:
                linked_list[i].next = linked_list[0]

        for i in range(len(linked_list)):
            if i == 0:
                linked_list[i].prev = linked_list[-1]
            else:
                linked_list[i].prev = linked_list[i - 1]

        self.linked_angle_current = linked_list[0]

    def __check_distance_to_target_point(self, node):
        x_full_difference = self.target_point.x() - node.point_expand.point.x()
        y_full_difference = self.target_point.y() - node.point_expand.point.y()
        return math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)

    def __update_node_by_target_vector(self, node):
        x_full_difference = self.target_point.x() - node.point_expand.point.x()
        y_full_difference = self.target_point.y() - node.point_expand.point.y()
        dist = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
        ev_x = x_full_difference / dist
        ev_y = y_full_difference / dist
        node.target_vector_x = ev_x * self.powerful_of_vector_to_target
        node.target_vector_y = ev_y * self.powerful_of_vector_to_target

    def __update_node_by_obstacles(self, node):
        for obstacle_geom in self.list_of_obstacles_apf:
            dist_to_obstacle = obstacle_geom.obstacle_geometry.distance(
                QgsGeometry.fromPointXY(node.point_expand.point))
            if dist_to_obstacle < self.length_from_obstacle_to_analysis:
                if node.min_dist_obstacle is None or dist_to_obstacle < node.min_dist_obstacle:
                    node.min_dist_obstacle = dist_to_obstacle
                    x_full_difference = node.point_expand.point.x() - obstacle_geom.centroid.x()
                    y_full_difference = node.point_expand.point.y() - obstacle_geom.centroid.y()
                    dist = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
                    ev_x = x_full_difference / dist
                    ev_y = y_full_difference / dist
                    node.obstacle_vector_x = ev_x * (
                            self.powerful_of_vector_from_obstacle * (
                            self.length_from_obstacle_to_analysis - dist_to_obstacle) /
                            self.length_from_obstacle_to_analysis)
                    node.obstacle_vector_y = ev_y * (
                            self.powerful_of_vector_from_obstacle * (
                            self.length_from_obstacle_to_analysis - dist_to_obstacle) /
                            self.length_from_obstacle_to_analysis)

    def __calculate_sum_vector_for_each_node(self):
        for node in self.all_nodes_list:
            if node.obstacle_vector_x is not None and node.obstacle_vector_y is not None:
                node.sum_vector_x = node.target_vector_x + node.obstacle_vector_x
                node.sum_vector_y = node.target_vector_y + node.obstacle_vector_y
            else:
                node.sum_vector_x = node.target_vector_x
                node.sum_vector_y = node.target_vector_y

    def __create_obstacle_apf(self):
        for o_geom in self.list_of_obstacles_geometry:
            self.list_of_obstacles_apf.append(ObstacleAPF(o_geom))

    def new_node_return(self, node, new_x, new_y, x, y):
        if [new_x, new_y] not in self.all_nodes_list_coor:
            point = QgsPointXY(node.point_expand.point.x() + x * self.point_search_distance,
                               node.point_expand.point.y() + y * self.point_search_distance)
            point_geometry = QgsGeometry.fromPointXY(point)

            cell = self.grid.define_point_using_math_search(point)
            if cell is not None:
                if cell.geometry is not None:
                    if self.hall.hall_polygon.distance(point_geometry) == 0 and (cell.geometry.distance(
                            point_geometry) > self.point_search_distance_diagonal) or cell.geometry.isNull():
                        point_expand = self.grid.get_point_expand_by_point(point)
                        if point_expand:
                            new_node = NodeAPF(point_expand, new_x, new_y)
                            return new_node
        return None

    def __get_next_point_by_angle(self, node, angle):
        right_priority = True
        while True:
            n = 360 - self.linked_angle_current.angle if self.linked_angle_current.angle + 45 > 360 else \
                self.linked_angle_current.angle + 45
            if self.linked_angle_current.angle <= angle < n:
                if self.linked_angle_current.angle <= angle < n / 2:
                    right_priority = False
                break
            elif self.linked_angle_current.angle == 337.5:
                if self.linked_angle_current.angle <= angle <= 360:
                    right_priority = False
                    break
                if 0 <= angle < 22.5:
                    break
                self.linked_angle_current = self.linked_angle_current.next
            else:
                self.linked_angle_current = self.linked_angle_current.next

        new_x = node.coordinate_int_x + self.linked_angle_current.add_x
        new_y = node.coordinate_int_y + self.linked_angle_current.add_y
        x = self.linked_angle_current.add_x
        y = self.linked_angle_current.add_y
        new_node = self.new_node_return(node, new_x, new_y, x, y)

        if new_node:
            return new_node
        else:
            right_ = self.linked_angle_current.next
            left_ = self.linked_angle_current.prev
            for _ in range(7):
                if right_priority:
                    right_priority = False
                    new_x = node.coordinate_int_x + right_.add_x
                    new_y = node.coordinate_int_y + right_.add_y
                    x = right_.add_x
                    y = right_.add_y
                    right_ = right_.next
                    new_node = self.new_node_return(node, new_x, new_y, x, y)
                    if new_node:
                        return new_node
                else:
                    right_priority = True
                    left_ = left_.prev
                    new_x = node.coordinate_int_x + left_.add_x
                    new_y = node.coordinate_int_y + left_.add_y
                    x = left_.add_x
                    y = left_.add_y
                    left_ = left_.next
                    new_node = self.new_node_return(node, new_x, new_y, x, y)
                    if new_node:
                        return new_node
        return None

    def __create_path_from_node_path(self):
        for i in range(len(self.path_list_points) - 1):
            line = QgsGeometry.fromPolylineXY([self.path_list_points[i].point_expand.point,
                                               self.path_list_points[i + 1].point_expand.point])
            self.list_of_path.append(line)

    def __find_path(self):
        start_point_expand = self.grid.get_point_expand_by_point(self.starting_point)
        start_node = NodeAPF(start_point_expand, 0, 0)
        self.path_list_points.append(start_node)

        current_node = start_node
        i = 0
        full_time = 0
        while full_time < self.time_to_succeed:
            time_current = time.perf_counter()
            self.all_nodes_list_coor.append([current_node.coordinate_int_x, current_node.coordinate_int_y])
            a = self.__check_distance_to_target_point(current_node)
            if self.__check_distance_to_target_point(current_node) < self.point_search_distance_diagonal:
                line = QgsGeometry.fromPolylineXY([current_node.point_expand.point,
                                                   self.target_point])
                geometry = self.grid.get_multipolygon_by_points(current_node.point_expand, self.target_point_expand)
                if geometry.distance(line):
                    self.path_list_points.append(NodeAPF(self.target_point_expand, 0, 0))
                    self.is_succes = True
                    break
                current_node.near_to_target = True

            self.__update_node_by_target_vector(current_node)
            self.__update_node_by_obstacles(current_node)
            current_node.calculate_sum()
            st = [current_node.sum_vector_x, current_node.sum_vector_y]
            vertical = [0, 1]
            angle = np.degrees(np.math.atan2(np.linalg.det([st, vertical]), np.dot(st, vertical)))

            if angle < 0:
                angle = 360 + angle

            current_node = self.__get_next_point_by_angle(current_node, angle)
            if not current_node:
                raise FailFindPathException("Path wasn`t found")
            self.path_list_points.append(current_node)

            full_time += time.perf_counter() - time_current
        else:
            raise TimeToSucceedException("Search is out of time")

        if not self.is_succes:
            raise FailFindPathException("Path wasn`t found")

    def run(self):
        self.debuglog.start_block("set geometry to the grid block")
        self._set_geometry_to_grid()
        self.debuglog.end_block("set geometry to the grid block")

        self.__create_obstacle_apf()

        self.debuglog.start_block("__create_linked_angle")
        self.__create_linked_angle()
        self.debuglog.end_block("__create_linked_angle")

        self.debuglog.start_block("__find_path")
        self.__find_path()
        self.debuglog.end_block("__find_path")

        self.__create_path_from_node_path()

        self.final_path = self.__get_shorter_path(self.list_of_path)

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
            points_geom = [QgsGeometry.fromPointXY(x.point_expand.point) for x in self.path_list_points]

            Visualizer.update_layer_by_geometry_objects(
                r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp", points_geom)
            list_of_lines = []
            for node in self.all_nodes_list:
                # To Delete
                line = QgsGeometry.fromPolylineXY([node.point_expand.point,
                                                   QgsPointXY(node.point_expand.point.x() + node.sum_vector_x,
                                                              node.point_expand.point.y() + node.sum_vector_y)])
                list_of_lines.append(line)
            Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp",
                                                        list_of_lines)

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
        point1 = QgsGeometry.fromPointXY(QgsPointXY(4428449.289396306, 5955808.191556434))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(4428453.513892108, 5955708.280828105))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = CoordinateTransform.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      False,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = APFMethodOptimize(find_path_data, debug_log)
        my_time_full = 0
        check.run()
        check.visualize()
        print(debug_log.get_info())
    my_time = (time.perf_counter() - my_time) / n
    print(my_time)
