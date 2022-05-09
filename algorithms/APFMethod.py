import math
import numpy as np
import time
from abc import ABC
from operator import attrgetter

from qgis.core import *
from algorithms.GdalUAV.transformation.coordinates.CoordinateTransform import CoordinateTransform
from ModuleInstruments.DebugLog import DebugLog
from algorithms.GdalUAV.processing.FindPathData import FindPathData
from algorithms.GdalUAV.base.MethodBasedOnHallAndGrid import MethodBasedOnHallAndGrid
from algorithms.GdalUAV.base.SearchMethodBase import SearchMethodBase
from algorithms.GdalUAV.exceptions.MethodsException import TimeToSucceedException, FailFindPathException
from algorithms.GdalUAV.processing.Converter import ObjectsConverter
from algorithms.GdalUAV.processing.GeometryPointExpand import GeometryPointExpand
from algorithms.GdalUAV.qgis.visualization.Visualizer import Visualizer


class NodeAPF:
    def __init__(self, point_expand, coordinate_int_x, coordinate_int_y):
        self.point_expand = point_expand
        self.coordinate_int_x = coordinate_int_x
        self.coordinate_int_y = coordinate_int_y
        self.target_vector_x = None
        self.tatget_vector_y = None
        self.obstacle_vector_x = None
        self.obstacle_vector_y = None
        self.sum_vector_x = None
        self.sum_vector_y = None
        self.min_dist_obstacle = None
        self.near_to_target = None


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


class APFMethod(MethodBasedOnHallAndGrid, SearchMethodBase, ABC):
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

        self.open_list = []
        self.closed_list = []
        self.all_nodes_list = []
        self.all_nodes_list_coor = []
        self.list_of_obstacles_apf = []
        self.last_node = None

        # self.search_range = [[-22.5, 22.5]: , [22.5, 67.5]: , [67.5, 112.5]: ,
        #                      [112.5, 157.5]: , [157.5, -157.5]: ,
        #                      [-22.5, -67.5]: , [-67.5, -112.5]: , [-112.5, -157.5]]
        self.linked_angle_current = None

        self.node_path = []
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

    def __new_neighbor(self, node, x, y):
        new_x = node.coordinate_int_x + x
        new_y = node.coordinate_int_y + y

        if not [new_x, new_y] in self.all_nodes_list_coor:
            point = QgsPointXY(node.point_expand.point.x() + x * self.point_search_distance,
                               node.point_expand.point.y() + y * self.point_search_distance)
            point_geometry = QgsGeometry.fromPointXY(point)

            cell = self.grid.define_point_using_math_search(point)
            if cell is not None:
                if self.hall.hall_polygon.distance(point_geometry) == 0 and ((cell.geometry.distance(
                        point_geometry) > self.point_search_distance_diagonal) or cell.geometry.isNull()):
                    point_expand = self.grid.get_point_expand_by_point(point)

                    if (x == 1 or x == -1) and (y == 1 or y == -1):
                        new_node = NodeAPF(point_expand, new_x, new_y)
                    else:
                        new_node = NodeAPF(point_expand, new_x, new_y)
                    self.open_list.append(new_node)
                    self.all_nodes_list.append(new_node)
                    self.all_nodes_list_coor.append([new_x, new_y])

    def __add_new_neighbors_to_surface(self, node):
        self.__new_neighbor(node, 1, 0)
        self.__new_neighbor(node, 1, 1)
        self.__new_neighbor(node, 0, 1)
        self.__new_neighbor(node, -1, 1)
        self.__new_neighbor(node, -1, 0)
        self.__new_neighbor(node, -1, -1)
        self.__new_neighbor(node, 0, -1)
        self.__new_neighbor(node, 1, -1)

    def __create_points_surface(self):
        start_point_expand = self.grid.get_point_expand_by_point(self.starting_point)
        start_node = NodeAPF(start_point_expand, 0, 0)
        self.open_list.append(start_node)
        self.all_nodes_list.append(start_node)
        self.all_nodes_list_coor.append([0, 0])
        while len(self.open_list) != 0:
            current_node = self.open_list[0]

            if self.__check_distance_to_target_point(current_node) < self.point_search_distance_diagonal:
                current_node.near_to_target = True

            self.open_list.remove(current_node)
            self.closed_list.append(current_node)

            self.__add_new_neighbors_to_surface(current_node)

    def __update_nodes_by_target_vector(self):
        for node in self.all_nodes_list:
            x_full_difference = self.target_point.x() - node.point_expand.point.x()
            y_full_difference = self.target_point.y() - node.point_expand.point.y()
            dist = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
            ev_x = x_full_difference / dist
            ev_y = y_full_difference / dist
            node.target_vector_x = ev_x * self.powerful_of_vector_to_target
            node.target_vector_y = ev_y * self.powerful_of_vector_to_target

    def __update_nodes_by_obstacles(self):
        for obstacle_geom in self.list_of_obstacles_apf:
            for node in self.all_nodes_list:
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

    def __get_next_point_by_angle(self, source_node, array, split_x, split_y, angle):
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

        get_node = array[source_node.coordinate_int_x + split_x + self.linked_angle_current.add_x][
            source_node.coordinate_int_y + split_y + self.linked_angle_current.add_y]
        if get_node != 0:
            array[source_node.coordinate_int_x + split_x][
                source_node.coordinate_int_y + split_y] = 0
            return get_node
        else:
            current_node = LinkedAngle(0)
            right_ = self.linked_angle_current.next
            left_ = self.linked_angle_current.prev
            for _ in range(7):
                if right_priority:
                    right_priority = False
                    right_ = right_.next
                    get_node = array[source_node.coordinate_int_x + split_x + right_.add_x][
                        source_node.coordinate_int_y + split_y + right_.add_y]
                    if get_node != 0:
                        array[source_node.coordinate_int_x + split_x][
                            source_node.coordinate_int_y + split_y] = 0
                        return get_node
                else:
                    right_priority = True
                    left_ = left_.prev
                    get_node = array[source_node.coordinate_int_x + split_x + left_.add_x][
                        source_node.coordinate_int_y + split_y + left_.add_y]
                    if get_node != 0:
                        array[source_node.coordinate_int_x + split_x][
                            source_node.coordinate_int_y + split_y] = 0
                        return get_node
        return None

    def __find_path(self):
        min_index_x = min(self.all_nodes_list, key=attrgetter('coordinate_int_x')).coordinate_int_x + 1
        min_index_y = min(self.all_nodes_list, key=attrgetter('coordinate_int_y')).coordinate_int_y + 1
        max_index_x = max(self.all_nodes_list, key=attrgetter('coordinate_int_x')).coordinate_int_x + 1
        max_index_y = max(self.all_nodes_list, key=attrgetter('coordinate_int_y')).coordinate_int_y + 1

        split_x = -min_index_x
        split_y = -min_index_y
        array = np.zeros((max_index_x + split_x + 1, max_index_y + split_y + 1), dtype=NodeAPF)
        for node in self.all_nodes_list:
            array[node.coordinate_int_x + split_x][node.coordinate_int_y + split_y] = node

        # coordinates [0, 0]
        node = array[split_x][split_y]
        self.node_path.append(node)
        st = [node.sum_vector_x, node.sum_vector_y]
        vertical = [0, 1]
        angle = np.degrees(np.math.atan2(np.linalg.det([st, vertical]), np.dot(st, vertical)))
        i = 0
        full_time = 0
        while full_time < self.time_to_succeed:
            time_current = time.perf_counter()
            if angle < 0:
                angle = 360 + angle
            node = self.__get_next_point_by_angle(node, array, split_x, split_y, angle)
            if node is None:
                raise FailFindPathException("Path wasn`t found")

            self.node_path.append(node)

            if node.near_to_target:
                line = QgsGeometry.fromPolylineXY([node.point_expand.point,
                                                   self.target_point])
                geometry = self.grid.get_multipolygon_by_points(node.point_expand, self.target_point_expand)
                if geometry.distance(line):
                    self.is_succes = True
                    break

            st = [node.sum_vector_x, node.sum_vector_y]
            angle = np.degrees(np.math.atan2(np.linalg.det([st, vertical]), np.dot(st, vertical)))
            full_time += time.perf_counter() - time_current
        else:
            raise TimeToSucceedException("Search is out of time")

    def __create_path_from_node_path(self):
        for i in range(len(self.node_path) - 1):
            line = QgsGeometry.fromPolylineXY([self.node_path[i].point_expand.point,
                                               self.node_path[i + 1].point_expand.point])
            self.list_of_path.append(line)

    def run(self):
        self.debuglog.start_block("set geometry to the grid block")
        self._set_geometry_to_grid()
        self.debuglog.end_block("set geometry to the grid block")

        self.debuglog.start_block("__create_linked_angle")
        self.__create_linked_angle()
        self.debuglog.end_block("__create_linked_angle")

        self.debuglog.start_block("create_points_surface")
        self.__create_points_surface()
        self.debuglog.end_block("create_points_surface")

        self.debuglog.start_block("__create_obstacle_apf")
        self.__create_obstacle_apf()
        self.debuglog.end_block("__create_obstacle_apf")

        self.debuglog.start_block("__update_nodes_by_target_vector")
        self.__update_nodes_by_target_vector()
        self.debuglog.end_block("__update_nodes_by_target_vector")

        self.debuglog.start_block("__update_nodes_by_obstacles")
        self.__update_nodes_by_obstacles()
        self.debuglog.end_block("__update_nodes_by_obstacles")

        self.debuglog.start_block("__calculate_sum_vector_for_each_node")
        self.__calculate_sum_vector_for_each_node()
        self.debuglog.end_block("__calculate_sum_vector_for_each_node")

        self.debuglog.start_block("__find_path")
        self.__find_path()
        self.debuglog.end_block("__find_path")
        if not self.is_succes:
            raise FailFindPathException("Path wasn`t found")

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
            points_geom = [QgsGeometry.fromPointXY(x.point_expand.point) for x in self.node_path]

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
        point1 = QgsGeometry.fromPointXY(QgsPointXY(4428248.30,5955188.71))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(4428369.89,5955263.35))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = CoordinateTransform.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      False,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = APFMethod(find_path_data, debug_log)
        my_time_full = 0
        check.run()
        check.visualize()
        print(debug_log.get_info())
    my_time = (time.perf_counter() - my_time) / n
    print(my_time)
