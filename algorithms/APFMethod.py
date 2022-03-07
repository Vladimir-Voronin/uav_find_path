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


class NodeAPF:
    def __init__(self, point_expand, coordinate_int_x, coordinate_int_y):
        self.point_expand = point_expand
        self.coordinate_int_x = coordinate_int_x
        self.coordinate_int_y = coordinate_int_y
        self.sum_vector_x = None
        self.sum_vector_y = None


class ObstacleAPF:
    def __init__(self, obstacle_geometry):
        self.obstacle_geometry = obstacle_geometry
        self.centroid = obstacle_geometry.centroid().asPoint()


class APFMethod(AlgoritmsBasedOnHallAndGrid, SearchAlgorithm, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        hall_width = 50
        super().__init__(findpathdata, debuglog, hall_width)

        cell_target = self.grid.difine_point(self.target_point_geometry)
        self.target_point_expand = GeometryPointExpand(self.target_point, cell_target.n_row,
                                                       cell_target.n_column)

        self.point_search_distance = 2
        self.point_search_distance_diagonal = self.point_search_distance * math.sqrt(2)

        self.length_from_obstacle_to_analysis = 10
        self.powerful_of_vector_to_target = 2
        self.powerful_of_vector_from_obstacle = 1.5

        self.open_list = []
        self.closed_list = []
        self.all_nodes_list = []
        self.all_nodes_list_coor = []
        self.list_of_obstacles_apf = []
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
        # match = filter(lambda node_: node_.coordinate_int_x == new_x and node_.coordinate_int_y == new_y,
        #                self.all_nodes_list)
        # first = next(match, None)

        if not [new_x, new_y] in self.all_nodes_list_coor:
            point = QgsPointXY(node.point_expand.point.x() + x * self.point_search_distance,
                               node.point_expand.point.y() + y * self.point_search_distance)
            point_geometry = QgsGeometry.fromPointXY(point)

            cell = self.grid.define_point_using_math_search(point)
            if cell is not None:
                if self.hall.hall_polygon.distance(point_geometry) == 0 and (cell.geometry.distance(
                        point_geometry) > self.point_search_distance_diagonal) or cell.geometry.isNull():
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
            self.open_list.remove(current_node)
            self.closed_list.append(current_node)

            self.__add_new_neighbors_to_surface(current_node)

    def __update_nodes_by_target_vector(self):
        # list_of_lines = []
        for node in self.all_nodes_list:
            x_full_difference = self.target_point.x() - node.point_expand.point.x()
            y_full_difference = self.target_point.y() - node.point_expand.point.y()
            dist = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
            ev_x = x_full_difference / dist
            ev_y = y_full_difference / dist
            node.sum_vector_x = ev_x * self.powerful_of_vector_to_target
            node.sum_vector_y = ev_y * self.powerful_of_vector_to_target

            # # To Delete
            # line = QgsGeometry.fromPolylineXY([node.point_expand.point,
            #                                    QgsPointXY(node.point_expand.point.x() + node.sum_vector_x,
            #                                               node.point_expand.point.y() + node.sum_vector_y)])
            # list_of_lines.append(line)
        # Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp",
        #                                             list_of_lines)

    def __update_nodes_by_obstacles(self):
        for obstacle_geom in self.list_of_obstacles_apf:
            for node in self.all_nodes_list:
                dist_to_obstacle = obstacle_geom.obstacle_geometry.distance(
                    QgsGeometry.fromPointXY(node.point_expand.point))
                if dist_to_obstacle < self.length_from_obstacle_to_analysis:
                    x_full_difference = node.point_expand.point.x() - obstacle_geom.centroid.x()
                    y_full_difference = node.point_expand.point.y() - obstacle_geom.centroid.y()
                    dist = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)
                    ev_x = x_full_difference / dist
                    ev_y = y_full_difference / dist
                    node.sum_vector_x = node.sum_vector_x + ev_x * (
                            self.powerful_of_vector_from_obstacle * dist_to_obstacle / self.length_from_obstacle_to_analysis)
                    node.sum_vector_y = node.sum_vector_y + ev_y * (
                            self.powerful_of_vector_from_obstacle * dist_to_obstacle / self.length_from_obstacle_to_analysis)

    # To delete visualise vectors
    def __visualise_vectors(self):
        list_of_lines = []
        for node in self.all_nodes_list:
            # To Delete
            line = QgsGeometry.fromPolylineXY([node.point_expand.point,
                                               QgsPointXY(node.point_expand.point.x() + node.sum_vector_x,
                                                          node.point_expand.point.y() + node.sum_vector_y)])
            list_of_lines.append(line)
        Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp",
                                                    list_of_lines)

    def __create_obstacle_apf(self):
        for o_geom in self.list_of_obstacles_geometry:
            self.list_of_obstacles_apf.append(ObstacleAPF(o_geom))

    def run(self):
        debug_log.start_block("set geometry to the grid block")
        self._set_geometry_to_grid()
        debug_log.end_block("set geometry to the grid block")

        debug_log.start_block("create_points_surface")
        self.__create_points_surface()
        debug_log.end_block("create_points_surface")

        debug_log.start_block("__create_obstacle_apf")
        self.__create_obstacle_apf()
        debug_log.end_block("__create_obstacle_apf")

        debug_log.start_block("__update_nodes_by_target_vector")
        self.__update_nodes_by_target_vector()
        debug_log.end_block("__update_nodes_by_target_vector")

        debug_log.start_block("__update_nodes_by_obstacles")
        self.__update_nodes_by_obstacles()
        debug_log.end_block("__update_nodes_by_obstacles")

        self.__visualise_vectors()

        points_geom = [QgsGeometry.fromPointXY(x.point_expand.point) for x in self.all_nodes_list]
        Visualizer.update_layer_by_geometry_objects(
            r"C:\Users\Neptune\Desktop\Voronin qgis\shp\points_import.shp", points_geom)

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
        point1 = QgsGeometry.fromPointXY(QgsPointXY(39.7867695, 47.2744990))
        point2 = QgsGeometry.fromPointXY(QgsPointXY(39.78598251, 47.27424235))
        path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

        obstacles = QgsVectorLayer(path)
        source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(obstacles, proj)
        find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp",
                                      False,
                                      source_list_of_geometry_obstacles)
        debug_log = DebugLog()
        check = APFMethod(find_path_data, debug_log)
        my_time_full = 0
        check.run()
        print(debug_log.get_info())
    my_time = (time.perf_counter() - my_time) / n
    print(my_time)
