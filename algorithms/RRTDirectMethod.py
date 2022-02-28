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
from algorithms.addition.GeometryPointExpand import GeometryPointExpand
from algorithms.addition.Visualizer import Visualizer


class RRTDirectMethod(AlgoritmsBasedOnHallAndGrid, SearchAlgorithm, ABC):
    def __init__(self, findpathdata: FindPathData, debuglog: DebugLog):
        super().__init__(findpathdata, debuglog)
        self.max_search_distance = 40

        cell_start = self.grid.difine_point(self.starting_point_geometry)
        self.start_point_expand = GeometryPointExpand(self.starting_point_geometry, cell_start.n_row,
                                                      cell_start.n_column)
        cell_target = self.grid.difine_point(self.starting_point_geometry)
        self.target_point_expand = GeometryPointExpand(self.target_point_geometry, cell_target.n_row,
                                                       cell_target.n_column)

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

    def __get_point_ahead(self, source_point_expand, target_point_expand):
        source_point = source_point_expand.point.asPoint()
        target_point = target_point_expand.point.asPoint()
        x_full_difference = target_point.x() - source_point.x()
        y_full_difference = target_point.y() - source_point.y()
        distance_between_points = math.sqrt(x_full_difference ** 2 + y_full_difference ** 2)

        if distance_between_points < self.max_search_distance:
            line = QgsGeometry.fromPolylineXY([source_point,
                                               target_point])
            geometry = self.grid.get_multipolygon_by_points(source_point, target_point_expand)
            if geometry.distance(line):
                # Add logic
                return line

        x_unit = x_full_difference / distance_between_points
        y_unit = y_full_difference / distance_between_points
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

        cell_for_new_point = self.grid.difine_point(self.starting_point_geometry)
        if cell_for_new_point is None:
            return None

        new_point_expand = GeometryPointExpand(new_point, cell_for_new_point.n_row,
                                               cell_for_new_point.n_column)

        geometry = self.grid.get_multipolygon_by_points(new_point_expand, target_point_expand)

        # Perhaps it will be faster if we skip this check (check for a line at once)
        if geometry.distance(new_point):
            line = QgsGeometry.fromPolylineXY([source_point,
                                               new_point.asPoint()])
            if geometry.distance(line):
                # Add logic
                return line
        return None

    def run(self):
        self._set_geometry_to_grid()

        list_of_lines_to_check = []
        my_time = time.perf_counter()
        for i in range(10000):
            p = self.__get_point_ahead(self.start_point_expand, self.target_point_expand)
            if p is not None:
                list_of_lines_to_check.append(p)
        my_time = time.perf_counter() - my_time

        print(list_of_lines_to_check)
        print(my_time)
        print(len(list_of_lines_to_check))
        Visualizer.update_layer_by_geometry_objects(r"C:\Users\Neptune\Desktop\Voronin qgis\shp\min_path.shp", list_of_lines_to_check)

    def visualise(self):
        pass


if __name__ == '__main__':
    QgsApplication.setPrefixPath(r'C:\OSGEO4~1\apps\qgis', True)
    qgs = QgsApplication([], False)
    qgs.initQgis()

    proj = QgsProject.instance()
    proj.read(r'C:\Users\Neptune\Desktop\Voronin qgis\Voronin qgis.qgs')
    point1 = QgsGeometry.fromPointXY(QgsPointXY(39.7658939,47.2779548))
    point2 = QgsGeometry.fromPointXY(QgsPointXY(39.764336, 47.273276))
    path = r"C:\Users\Neptune\Desktop\Voronin qgis\shp\Строения.shp"

    obstacles = QgsVectorLayer(path)
    source_list_of_geometry_obstacles = Converter.get_list_of_poligons_in_3395(obstacles, proj)
    find_path_data = FindPathData(proj, point1, point2, obstacles, r"C:\Users\Neptune\Desktop\Voronin qgis\shp", False,
                                  source_list_of_geometry_obstacles)
    debug_log = DebugLog()
    check = RRTDirectMethod(find_path_data, debug_log)
    check.run()
