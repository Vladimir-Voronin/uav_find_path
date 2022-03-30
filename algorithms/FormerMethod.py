import math
import random
from _ctypes import sizeof

import numpy as np
import time
from abc import ABC
from operator import attrgetter

import sys
from memory_profiler import profile
from qgis.core import *
from ModuleInstruments.Converter import Converter
from ModuleInstruments.DebugLog import DebugLog
from ModuleInstruments.FindPathData import FindPathData
from algorithms.BaseAlgorithims.AlgorithmsBasedOnHallAndGrid import AlgoritmsBasedOnHallAndGrid
from algorithms.BaseAlgorithims.SearchAlgorthim import SearchAlgorithm
from algorithms.GdalFPExtension.exceptions.MethodsException import FailFindPathException
from algorithms.GdalFPExtension.gdalObjects.Converter import ObjectsConverter
from algorithms.GdalFPExtension.gdalObjects.GeometryPointExpand import GeometryPointExpand
from algorithms.GdalFPExtension.qgis.visualization.Visualizer import Visualizer


class NodeFormer:
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


class AntVertex:
    def __init__(self, point: QgsPointXY, coor_x, coor_y, near_to_target):
        self.point = point
        self.coor_x = coor_x
        self.coor_y = coor_y
        self.near_to_target = near_to_target
        self.edges = []

    def get_max_pheromones(self):
        return max(self.edges, key=lambda x: x.pheromone_value)


class AntEdge:
    def __init__(self, one_vertex: AntVertex, another_vertex: AntVertex):
        self.one_vertex = one_vertex
        self.another_vertex = another_vertex
        self.pheromone_value = 0


class AntGraph:
    def __init__(self, array, start_vertex, decr_coef, expire_coef):
        self.array = array
        self.start_vertex = start_vertex
        if 0 >= decr_coef >= 1:
            raise ValueError("decr coef should be between 0 and 1 (but not equal to them)")
        self.dect_coef = decr_coef
        self.expire_coef = expire_coef

        self.all_verteces = []
        for i in range(len(array) - 1):
            for k in range(len(array[i]) - 1):
                if type(array[i][k]) is AntVertex:
                    self.all_verteces.append(array[i][k])

        self.target_verteces = []
        for i in range(len(self.array) - 1):
            for k in range(len(self.array[i]) - 1):
                if type(self.array[i][k]) is AntVertex and self.array[i][k].near_to_target:
                    self.target_verteces.append(self.array[i][k])
                    break

        for ver in self.target_verteces:
            for edge in ver.edges:
                edge.pheromone_value = 1

    def one_random_step(self, vertex):
        rand_edge = random.choice(vertex.edges)
        v_next = None
        if vertex == rand_edge.one_vertex:
            v_next = rand_edge.another_vertex
        elif vertex == rand_edge.another_vertex:
            v_next = rand_edge.one_vertex

        rand_edge.pheromone_value = max(rand_edge.pheromone_value,
                                        v_next.get_max_pheromones().pheromone_value * self.dect_coef)
        # rand_edge.pheromone_value = rand_edge.pheromone_value * (
        #             1 - self.dect_coef) + v_next.get_max_pheromones().pheromone_value * self.dect_coef
        return v_next

    def one_real_step(self, vertex):
        max_value = -1
        edge = None
        for e in vertex.edges:
            if e.pheromone_value > max_value:
                max_value = e.pheromone_value
                edge = e
            elif e.pheromone_value == max_value:
                get_it = random.randint(0, 1)
                if get_it:
                    edge = e

        v_next = None
        if vertex == edge.one_vertex:
            v_next = edge.another_vertex
        elif vertex == edge.another_vertex:
            v_next = edge.one_vertex

        edge.pheromone_value = max(edge.pheromone_value,
                                   v_next.get_max_pheromones().pheromone_value * self.dect_coef)
        # edge.pheromone_value = edge.pheromone_value * (
        #             1 - self.dect_coef) + v_next.get_max_pheromones().pheromone_value * self.dect_coef
        return v_next, edge

    def investigation_from_vertex(self, vertex_begin, number_of_steps):
        for i in range(number_of_steps):
            vertex_begin = self.one_random_step(vertex_begin)
        return vertex_begin

    def search_from_start_to_target(self, max_number_of_iterations):
        vertex_begin = self.start_vertex
        for i in range(max_number_of_iterations):
            vertex_begin, edge = self.one_real_step(vertex_begin)
            if vertex_begin in self.target_verteces:
                break

    def contest(self, number_of_ants_to_contest, max_number_of_iterations):
        edges_to_upgrade = [x for x in range(len(self.all_verteces) * 8)]
        for ant in range(number_of_ants_to_contest):
            current_edges = []
            vertex_begin = self.start_vertex
            for i in range(max_number_of_iterations):
                vertex_begin, edge = self.one_real_step(vertex_begin)
                current_edges.append(edge)
                if vertex_begin in self.target_verteces:
                    if len(current_edges) < len(edges_to_upgrade):
                        edges_to_upgrade = current_edges.copy()
                    break
        for edge in edges_to_upgrade:
            edge.pheromone_value += edge.pheromone_value * ((1 - self.expire_coef) / 3)

    def expire(self):
        for i in self.all_verteces:
            for e in i.edges:
                e.pheromone_value = e.pheromone_value * self.expire_coef

    def get_real_path(self, max_number_of_iterations):
        path_by_vertex = []
        is_ok = False
        vertex_begin = self.start_vertex
        path_by_vertex.append(vertex_begin)
        for i in range(max_number_of_iterations):
            vertex_begin, edge = self.one_real_step(vertex_begin)
            path_by_vertex.append(vertex_begin)
            if vertex_begin in self.target_verteces:
                is_ok = True
                break

        if not is_ok:
            raise FailFindPathException("Need more investigations in this matrix")

        points_path = []
        for i in path_by_vertex:
            points_path.append(i.point)
        return points_path


class FormerMethod(AlgoritmsBasedOnHallAndGrid, SearchAlgorithm, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 50
        super().__init__(findpathdata, debuglog, hall_width)

        cell_target = self.grid.difine_point(self.target_point_geometry)
        self.target_point_expand = GeometryPointExpand(self.target_point, cell_target.n_row,
                                                       cell_target.n_column)

        self.point_search_distance = 3
        self.point_search_distance_diagonal = self.point_search_distance * math.sqrt(2)

        self.open_list = []
        self.closed_list = []
        self.all_nodes_list = []
        self.all_nodes_list_coor = []

        self.node_path = []
        self.list_of_path = []
        self.final_path = []

    def __create_grid(self):
        self.debuglog.start_block("create grid")
        super()._create_grid()
        self.debuglog.end_block("create grid")

    def __get_shorter_path(self, feats, increase_points=0):
        self.debuglog.start_block("get shorter path")
        result = super()._get_shorter_path(feats, increase_points)
        self.debuglog.end_block("get shorter path")
        return result

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
                        new_node = NodeFormer(point_expand, new_x, new_y)
                    else:
                        new_node = NodeFormer(point_expand, new_x, new_y)
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
        start_node = NodeFormer(start_point_expand, 0, 0)
        self.open_list.append(start_node)
        self.all_nodes_list.append(start_node)
        self.all_nodes_list_coor.append([0, 0])

        the_end_is_achived = False
        while len(self.open_list) != 0:
            current_node = self.open_list[0]

            if self.__check_distance_to_target_point(current_node) < self.point_search_distance_diagonal:
                line = QgsGeometry.fromPolylineXY([current_node.point_expand.point,
                                                   self.target_point])
                geometry = self.grid.get_multipolygon_by_points(current_node.point_expand, self.target_point_expand)
                if geometry.distance(line):
                    current_node.near_to_target = True
                    the_end_is_achived = True
            self.open_list.remove(current_node)
            self.closed_list.append(current_node)

            self.__add_new_neighbors_to_surface(current_node)

        if not the_end_is_achived:
            raise FailFindPathException("Target point cant be achieved with those paramets")

    def __find_path(self):
        min_index_x = min(self.all_nodes_list, key=attrgetter('coordinate_int_x')).coordinate_int_x + 1
        min_index_y = min(self.all_nodes_list, key=attrgetter('coordinate_int_y')).coordinate_int_y + 1
        max_index_x = max(self.all_nodes_list, key=attrgetter('coordinate_int_x')).coordinate_int_x + 1
        max_index_y = max(self.all_nodes_list, key=attrgetter('coordinate_int_y')).coordinate_int_y + 1

        split_x = -min_index_x
        split_y = -min_index_y
        array = np.zeros((max_index_x + split_x + 1, max_index_y + split_y + 1), dtype=AntVertex)
        for node in self.all_nodes_list:
            array[node.coordinate_int_x + split_x][node.coordinate_int_y + split_y] = AntVertex(
                node.point_expand.point, node.coordinate_int_x + split_x, node.coordinate_int_y + split_y,
                node.near_to_target)

        for i in range(len(array) - 1):
            for k in range(len(array[i]) - 1):
                if type(array[i][k]) is AntVertex:
                    if type(array[i][k + 1]) is AntVertex:
                        new_edg = AntEdge(array[i][k], array[i][k + 1])
                        array[i][k].edges.append(new_edg)
                        array[i][k + 1].edges.append(new_edg)
                    if type(array[i + 1][k + 1]) is AntVertex:
                        new_edg = AntEdge(array[i][k], array[i + 1][k + 1])
                        array[i][k].edges.append(new_edg)
                        array[i + 1][k + 1].edges.append(new_edg)
                    if type(array[i + 1][k]) is AntVertex:
                        new_edg = AntEdge(array[i][k], array[i + 1][k])
                        array[i][k].edges.append(new_edg)
                        array[i + 1][k].edges.append(new_edg)
                    if type(array[i - 1][k + 1]) is AntVertex:
                        new_edg = AntEdge(array[i][k], array[i - 1][k + 1])
                        array[i][k].edges.append(new_edg)
                        array[i - 1][k + 1].edges.append(new_edg)

        # coordinates [0, 0]
        start_v = array[split_x][split_y]

        ant_graph = AntGraph(array, start_v, 0.95, 0.98)
        for i in range(5):
            ant_graph.investigation_from_vertex(random.choice(ant_graph.target_verteces),
                                                len(ant_graph.all_verteces) * 5)
        ant_graph.expire()
        for i in range(len(ant_graph.all_verteces)):
            ant_graph.investigation_from_vertex(random.choice(ant_graph.all_verteces), 100)

        ant_graph.expire()
        for i in range(50):
            ant_graph.investigation_from_vertex(ant_graph.start_vertex, len(ant_graph.all_verteces))
            ant_graph.search_from_start_to_target(len(ant_graph.all_verteces))

        ant_graph.expire()
        # self.visualize_ant_edges(array)

        points_path = ant_graph.get_real_path(len(ant_graph.all_verteces))
        return points_path

    def __create_path_from_points(self, points_list):
        for i in range(len(points_list) - 1):
            line = QgsGeometry.fromPolylineXY([points_list[i],
                                               points_list[i + 1]])
            self.list_of_path.append(line)

    def run(self):
        self.debuglog.start_block("set geometry to the grid block")
        self._set_geometry_to_grid()
        self.debuglog.end_block("set geometry to the grid block")

        self.debuglog.start_block("create_points_surface")
        self.__create_points_surface()
        self.debuglog.end_block("create_points_surface")

        self.debuglog.start_block("__find_path")
        points_path = self.__find_path()
        self.debuglog.end_block("__find_path")

        self.__create_path_from_points(points_path)

        self.final_path = self.__get_shorter_path(self.list_of_path)

    def visualize_ant_edges(self, array):
        list_to_visualise = []
        for i in range(len(array) - 1):
            for k in range(len(array[i]) - 1):
                if type(array[i][k]) is AntVertex:
                    for e in array[i][k].edges:
                        list_to_visualise.append(e)

        layer = QgsVectorLayer(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\check_line.shp")
        features = []
        for ed in list_to_visualise:
            feat = QgsFeature(layer.fields())
            feat.setGeometry(QgsGeometry.fromPolylineXY([ed.one_vertex.point, ed.another_vertex.point]))
            feat.setAttribute('ant_weight', round(ed.pheromone_value, 8))
            features.append(feat)

        Visualizer.update_layer_by_feats_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\check_line.shp",
                                                 features)

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
        point1 = QgsGeometry.fromPointXY(QgsPointXY(4427959.83, 5955014.48))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(4428148.92, 5955194.46))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      False,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = FormerMethod(find_path_data, debug_log)
        my_time_full = 0
        check.run()
        check.visualize()
        print(debug_log.get_info())
    my_time = (time.perf_counter() - my_time) / n
    print(my_time)
